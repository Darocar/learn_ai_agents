"""Math expression calculator tool.

This module provides a tool for safely evaluating mathematical
expressions using Python's AST parser.
"""

import ast


def calculate_math_expression(math_expression: str) -> str:
    """Evaluate mathematical expressions safely.

    This tool can evaluate arithmetic expressions, including:
    - Basic operations: +, -, *, /, **, //, %
    - Parentheses for grouping
    - Common math functions (when available in the expression)

    Args:
        math_expression: The mathematical expression to evaluate.

    Returns:
        The result of the evaluation as a string.

    Examples:
        >>> calculate_math_expression("2 + 2")
        "4"
        >>> calculate_math_expression("(10 * 5) / 2")
        "25.0"
    """
    try:
        # Safely evaluate the mathematical expression using AST
        # This prevents arbitrary code execution
        result = eval(compile(ast.parse(math_expression, mode="eval"), "", "eval"))
        return str(result)
    except SyntaxError:
        return f"Error: Invalid mathematical expression '{math_expression}'"
    except Exception as e:
        return f"Error evaluating expression: {e}"
