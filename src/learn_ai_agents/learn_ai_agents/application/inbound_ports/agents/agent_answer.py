"""
Inbound Port: BasicAnswerPort

HEXAGONAL ARCHITECTURE ROLE: INBOUND PORT (Entry Point Interface)
===================================================================

This is an INBOUND PORT in hexagonal architecture. Think of it as the "front door"
of your application's core business logic.

What is an Inbound Port?
-------------------------
- An INTERFACE that defines what operations the application offers to the outside world
- Called BY external adapters (like HTTP controllers, CLI handlers, message queues)
- Implemented BY use cases in the application layer
- Uses DTOs (Data Transfer Objects) to decouple from transport mechanisms

Why Inbound Ports?
------------------
1. DECOUPLING: Controllers don't depend on concrete implementations
2. TESTABILITY: Easy to create mock/fake implementations for testing
3. FLEXIBILITY: Multiple adapters can call the same port (HTTP, CLI, gRPC, etc.)
4. CLARITY: Explicitly defines the application's capabilities

The Flow:
---------
    External World (HTTP, CLI, etc.)
            ↓
    Inbound Adapter (Controller)
            ↓
    Inbound Port (THIS FILE) ← You are here!
            ↓
    Use Case (Implementation)
            ↓
    Application Core

In this file:
-------------
We define the BasicAnswerPort protocol which specifies:
- invoke(): Synchronous question answering
- stream(): Streaming question answering with real-time chunks
"""

from collections.abc import AsyncIterator, Iterable
from typing import Protocol

from learn_ai_agents.application.dtos.agents.basic_answer import AnswerRequestDTO, AnswerResultDTO, AnswerStreamEventDTO


class AgentAnswerPort(Protocol):
    """
    Port (Interface) for basic question-answering functionality.

    HEXAGONAL ARCHITECTURE: This is an INBOUND PORT
    ------------------------------------------------
    - Defines WHAT the application can do (answer questions)
    - Controllers CALL this interface
    - Use cases IMPLEMENT this interface
    - Uses DTOs to stay independent of HTTP/JSON/transport concerns

    Pattern: Protocol (Structural Subtyping)
    ----------------------------------------
    We use Python's Protocol instead of ABC because:
    - More Pythonic (duck typing with type safety)
    - No need for explicit inheritance
    - Easier to create test doubles (mocks/fakes)
    - More flexible for implementations

    Methods:
    --------
    invoke() : Synchronous request/response (deprecated)
    stream() : Synchronous streaming (deprecated)
    ainvoke() : Async request/response
    astream() : Async streaming with Server-Sent Events
    """

    def invoke(self, cmd: AnswerRequestDTO) -> AnswerResultDTO:
        """
        Handle a question synchronously and return a complete answer.

        DEPRECATED: Use ainvoke() instead.

        Args:
            cmd (AnswerRequestDTO): Request containing the user's question

        Returns:
            AnswerResultDTO: Response containing the agent's answer
        """
        ...

    def stream(self, cmd: AnswerRequestDTO) -> Iterable[AnswerStreamEventDTO]:
        """
        Handle a question with streaming response for real-time feedback.

        DEPRECATED: Use astream() instead.

        Args:
            cmd (AnswerRequestDTO): Same as invoke(), but response streams

        Yields:
            AnswerStreamEventDTO: Stream events (deltas and completion signal)
        """
        ...

    async def ainvoke(self, cmd: AnswerRequestDTO) -> AnswerResultDTO:
        """
        Handle a question asynchronously and return a complete answer.

        Args:
            cmd (AnswerRequestDTO): Request containing the user's question

        Returns:
            AnswerResultDTO: Response containing the agent's answer
        """
        ...

    async def astream(self, cmd: AnswerRequestDTO) -> AsyncIterator[AnswerStreamEventDTO]:
        """
        Handle a question with async streaming response for real-time feedback.

        Args:
            cmd (AnswerRequestDTO): Same as ainvoke(), but response streams

        Yields:
            AnswerStreamEventDTO: Stream events (deltas and completion signal)
        """
        ...
