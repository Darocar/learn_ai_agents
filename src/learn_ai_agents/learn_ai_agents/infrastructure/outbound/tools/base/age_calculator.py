"""Age calculator tool.

This module provides a tool for calculating age based on a birth date.
"""

from datetime import datetime


def calculate_age(birth_date: str) -> str:
    """Calculate age based on birth date.

    This tool calculates the current age in years based on the provided birth date.

    Args:
        birth_date: The birth date in yyyy-mm-dd format (e.g., '1990-05-15').

    Returns:
        A string describing the calculated age.

    Examples:
        >>> calculate_age("1990-01-01")
        "You are 34 years old."
        >>> calculate_age("2000-12-25")
        "You are 24 years old."
    """
    try:
        # Parse the birth date
        birth = datetime.strptime(birth_date, "%Y-%m-%d")

        # Get current date
        today = datetime.now()

        # Calculate age
        age = today.year - birth.year

        # Adjust if birthday hasn't occurred this year yet
        if (today.month, today.day) < (birth.month, birth.day):
            age -= 1

        if age < 0:
            return f"Error: The birth date '{birth_date}' is in the future."

        return f"{age} years old."

    except ValueError:
        return f"Error: Invalid date format '{birth_date}'. Please use yyyy-mm-dd format (e.g., '1990-05-15')."
    except Exception as e:
        return f"Error calculating age: {e}"
