"""
Domain Layer

The core business logic layer that is independent of external frameworks and infrastructure.
This layer contains:
- Business models (entities, value objects)
- Domain exceptions
- Domain services (business rules that don't belong to a single entity)

Following Hexagonal Architecture principles, this layer should have NO dependencies
on external libraries or frameworks (except for basic Python utilities).
"""
