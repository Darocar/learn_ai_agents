"""
Domain Exceptions

Custom exceptions that represent business rule violations or domain errors.
"""


class DomainException(Exception):
    """Base exception for all domain-related errors."""
    pass


class ValidationError(DomainException):
    """Raised when domain validation rules are violated."""
    pass
