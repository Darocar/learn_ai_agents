"""
Infrastructure Layer

The infrastructure layer contains all the external-facing implementations:
- Inbound adapters (REST controllers, CLI handlers, message consumers)
- Outbound adapters (database repositories, external API clients)
- Framework-specific configuration and bootstrap code

This layer depends on both the application and domain layers and contains
all framework-specific code (FastAPI, database ORMs, etc.).
"""
