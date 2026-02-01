"""Fake embedder adapter for testing.

This module provides a deterministic fake implementation of embedders.
Returns deterministic vectors based on input text without external models.
"""

import json
from pathlib import Path
from typing import Dict, List, Union

from learn_ai_agents.application.outbound_ports.content_indexer.embedders.embedder import (
    EmbedderPort,
)


class FakeEmbedder(EmbedderPort):
    """Simple deterministic embedder for tests.

    - No external models
    - Deterministic vectors based on input text
    - Fast and fully in-memory
    """

    def __init__(self, vector_size: int = 8, model_name: str = "fake-embedder", device: str = "cpu", **kwargs):
        """Initialize fake embedder.
        
        Args:
            vector_size: Dimensionality of embedding vectors.
            model_name: Name to return for the model.
            device: Device parameter (ignored, for compatibility).
            **kwargs: Additional arguments (ignored).
        """
        self.vector_size = vector_size
        self.model_name = model_name
        self.device = device
        self.calls: List[List[str]] = []  # to assert which texts were embedded
        self._preloaded_embeddings: Dict[str, List[float]] = {}  # text -> vector mapping

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate deterministic embeddings for texts.
        
        If texts are preloaded from file, returns those vectors.
        Otherwise generates deterministic vectors based on text content.
        
        Args:
            texts: List of texts to embed.
            
        Returns:
            List of embedding vectors (same length as input texts).
        """
        self.calls.append(texts)

        vectors: List[List[float]] = []
        for text in texts:
            # Check if we have a preloaded embedding for this text
            if text in self._preloaded_embeddings:
                vectors.append(self._preloaded_embeddings[text])
            else:
                # Generate deterministic vector based on text content
                base = sum(ord(c) for c in text)
                vec = [(base + i) / 1000.0 for i in range(self.vector_size)]
                vectors.append(vec)
        return vectors

    def get_dimensions(self) -> int:
        """Get the dimensionality of embeddings.
        
        Returns:
            Vector size.
        """
        return self.vector_size

    def get_model_name(self) -> str:
        """Get the model name.
        
        Returns:
            Model name string.
        """
        return self.model_name
    
    def get_call_count(self) -> int:
        """Get the number of times embed_texts was called.
        
        Returns:
            Number of calls.
        """
        return len(self.calls)
    
    def get_all_embedded_texts(self) -> List[str]:
        """Get all texts that were embedded.
        
        Returns:
            Flattened list of all embedded texts.
        """
        return [text for call in self.calls for text in call]
    
    def clear_calls(self) -> None:
        """Clear the call history."""
        self.calls.clear()
    
    def load_from_file(self, file_path: Union[str, Path]) -> None:
        """Load precomputed embeddings from a JSON file.
        
        Expected JSON format:
        {
            "text1": [0.1, 0.2, ...],
            "text2": [0.3, 0.4, ...],
            ...
        }
        
        or
        
        [
            {"text": "text1", "vector": [0.1, 0.2, ...]},
            {"text": "text2", "vector": [0.3, 0.4, ...]},
            ...
        ]
        
        Args:
            file_path: Path to JSON file with embeddings.
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Embeddings file not found: {file_path}")
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        if isinstance(data, dict):
            # Format: {"text": [vector]}
            self._preloaded_embeddings = data
        elif isinstance(data, list):
            # Format: [{"text": "...", "vector": [...]}]
            for item in data:
                text = item.get("text", "")
                vector = item.get("vector", [])
                if text and vector:
                    self._preloaded_embeddings[text] = vector
        else:
            raise ValueError(f"Invalid embeddings file format. Expected dict or list, got {type(data)}")
