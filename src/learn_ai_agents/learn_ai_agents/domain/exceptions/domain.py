from typing import Dict, Any, Optional

from ._base import BusinessRuleException


class ResourceNotFoundException(BusinessRuleException):
    """
    Exception raised when a requested resource is not found.
    """

    def __init__(self, resource_type: str, resource_id: str):
        message = f"{resource_type} with ID '{resource_id}' not found."
        super().__init__(message, details={"resource_type": resource_type, "resource_id": resource_id})


class InvalidRequestException(BusinessRuleException):
    """
    Exception raised for invalid requests.
    """

    def __init__(self,  message: str = "Invalid request parameters.", params: Optional[Dict[str, Any]] = None):
        super().__init__(message, details={"params": params} if params else {})


class SourceContentFormatException(BusinessRuleException):
    """
    Exception raised when the source content format is invalid or unsupported.
    """

    def __init__(self, content_type: str, message: str = "Unsupported or invalid content format."):
        super().__init__(message, details={"content_type": content_type})