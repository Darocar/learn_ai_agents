"""
Inbound Port: CharacterChatPort

HEXAGONAL ARCHITECTURE ROLE: INBOUND PORT (Entry Point Interface)
===================================================================

This is an INBOUND PORT in hexagonal architecture for chatting with
Baldur's Gate 3 characters using RAG (Retrieval-Augmented Generation).

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
We define the CharacterChatPort protocol which specifies:
- ainvoke(): Async question answering for character chat
- astream(): Async streaming question answering with real-time chunks
"""

from collections.abc import AsyncIterator
from typing import Protocol

from learn_ai_agents.application.dtos.agents.character_chat import (
    CharacterChatRequestDTO,
    CharacterChatResultDTO,
    CharacterChatStreamEventDTO,
)


class CharacterChatPort(Protocol):
    """
    Port (Interface) for BG3 character chat functionality.

    HEXAGONAL ARCHITECTURE: This is an INBOUND PORT
    ------------------------------------------------
    - Defines WHAT the application can do (chat with BG3 characters using RAG)
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
    ainvoke() : Async request/response
    astream() : Async streaming with Server-Sent Events
    """

    async def ainvoke(self, cmd: CharacterChatRequestDTO) -> CharacterChatResultDTO:
        """
        Handle a character chat request asynchronously and return a complete answer.

        Args:
            cmd (CharacterChatRequestDTO): Request containing the user's message,
                character name, and document ID for RAG.

        Returns:
            CharacterChatResultDTO: Response containing the character's answer.
        """
        ...

    async def astream(self, cmd: CharacterChatRequestDTO) -> AsyncIterator[CharacterChatStreamEventDTO]:
        """
        Handle a character chat request with async streaming response for real-time feedback.

        Args:
            cmd (CharacterChatRequestDTO): Same as ainvoke(), but response streams.

        Yields:
            CharacterChatStreamEventDTO: Stream events (deltas and completion signal).
        """
        ...
