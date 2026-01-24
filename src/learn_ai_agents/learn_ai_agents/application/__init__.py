"""
Application Layer

The application layer orchestrates the flow of data between the domain layer
and the outside world. It contains:
- Use cases (application-specific business rules)
- DTOs (Data Transfer Objects for input/output)
- Port interfaces (abstractions for external dependencies)

This layer depends on the domain layer but is independent of specific implementations.
"""
