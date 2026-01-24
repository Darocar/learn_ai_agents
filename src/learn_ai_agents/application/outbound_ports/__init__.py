"""
Outbound Ports

Outbound ports are interfaces that define how the application interacts with
external systems (databases, APIs, file systems, etc.).

The application layer defines these interfaces, but the infrastructure layer
provides the actual implementations (adapters).

This follows the Dependency Inversion Principle: the application layer
defines what it needs, and the infrastructure layer provides it.
"""
