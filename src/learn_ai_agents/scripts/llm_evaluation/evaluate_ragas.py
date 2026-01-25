"""Simple script to evaluate RAG datasets using ragas metrics."""

import asyncio
import json
import os
from pathlib import Path
from dotenv import load_dotenv

from openai import AsyncOpenAI
from ragas.llms import llm_factory
from ragas.metrics.collections import ContextPrecision, Faithfulness


async def load_dataset(file_path: Path) -> dict:
    """Load a single dataset file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


async def evaluate_dataset(dataset: dict, dataset_name: str, llm) -> dict:
    """Evaluate a single dataset with ragas metrics."""
    print(f"\n{'='*60}")
    print(f"Evaluating: {dataset_name}")
    print(f"{'='*60}")
    
    # Initialize metrics
    context_precision = ContextPrecision(llm=llm)
    faithfulness = Faithfulness(llm=llm)
    
    print("\nEvaluating Context Precision...")
    precision_result = await context_precision.ascore(
        user_input=dataset["user_input"],
        reference=dataset["reference"],
        retrieved_contexts=dataset["retrieved_contexts"]
    )
    
    print("Evaluating Faithfulness...")
    # Ideally dataset should contain the actual model/agent output in "response"
    faithfulness_result = await faithfulness.ascore(
        user_input=dataset["user_input"],
        response=dataset.get("response", dataset["reference"]),
        retrieved_contexts=dataset["retrieved_contexts"]
    )
    
    results = {
        "dataset_name": dataset_name,
        "user_input": dataset["user_input"],
        "context_precision": precision_result.value,
        "faithfulness": faithfulness_result.value,
    }
    
    print(f"\nResults for {dataset_name}:")
    print(f"  Context Precision: {precision_result.value:.4f}")
    print(f"  Faithfulness:      {faithfulness_result.value:.4f}")
    
    return results


async def main():
    """Main evaluation function."""
    load_dotenv()
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY environment variable not set")
    
    # Groq OpenAI-compatible endpoint
    client = AsyncOpenAI(
        api_key=groq_api_key,
        base_url="https://api.groq.com/openai/v1",
    )
    
    llm = llm_factory(
        "llama-3.3-70b-versatile",
        provider="openai",
        client=client,
    )
    
    # Define paths
    datasets_dir = Path(__file__).parent.parent.parent / "data" / "llm_evaluation" / "datasets"
    results_dir = Path(__file__).parent.parent.parent / "data" / "llm_evaluation" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all JSON dataset files
    dataset_files = list(datasets_dir.glob("*.json"))
    
    if not dataset_files:
        print("No dataset files found!")
        return
    
    print(f"Found {len(dataset_files)} dataset(s) to evaluate")
    
    # Evaluate each dataset
    all_results = []
    for dataset_file in dataset_files:
        dataset = await load_dataset(dataset_file)
        result = await evaluate_dataset(dataset, dataset_file.stem, llm)
        all_results.append(result)
    
    # Save results
    output_file = results_dir / "ragas_evaluation_results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*60}")
    print(f"Results saved to: {output_file}")
    print(f"{'='*60}")
    
    # Print summary
    print("\nSummary:")
    print(f"{'Dataset':<30} {'Context Precision':<20} {'Faithfulness':<15}")
    print("-" * 65)
    for result in all_results:
        print(f"{result['dataset_name']:<30} {result['context_precision']:<20.4f} {result['faithfulness']:<15.4f}")


if __name__ == "__main__":
    asyncio.run(main())
