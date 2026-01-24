from ._base import ComponentException


# --- Family/Hierarchical Exceptions ---

class ComponentBuildingException(ComponentException):
    """
    Base exception for errors during component construction/initialization.
    Use this family for build-time errors (loading models, initializing resources, etc.).
    """
    pass


class ComponentConnectionException(ComponentException):
    """
    Base exception for errors during component connection establishment.
    Use this family for connection-related errors (database, external services, etc.).
    """
    pass


class ComponentOperationException(ComponentException):
    """
    Base exception for errors during component operations.
    Use this family for runtime operation errors (queries, processing, disconnection, etc.).
    """
    pass



class ComponentNotAvailableException(ComponentException):
    """
    Exception raised when a required component is not available or fails unexpectedly.
    Use this for cases like 500 errors, service unavailability, or unexpected component failures.
    """
    pass


class ComponentValidationException(ComponentException):
    """
    Exception raised when component receives invalid configuration or parameters.
    Use this for cases like invalid settings, malformed input, or configuration validation failures.
    This is distinct from ComponentBuildingException which is for initialization failures.
    """
    pass