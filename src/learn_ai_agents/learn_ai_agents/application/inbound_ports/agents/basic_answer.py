"""Inbound port for basic answer functionality."""

from collections.abc import AsyncIterable
from typing import Protocol

from learn_ai_agents.application.dtos.agents.basic_answer import AnswerRequestDTO, AnswerResultDTO, AnswerStreamEventDTO


class BasicAnswerPort(Protocol):
    """Inbound port for basic question-answering functionality."""

    async def ainvoke(self, cmd: AnswerRequestDTO) -> AnswerResultDTO:
        """Process a question and return the answer asynchronously."""
        ...

    async def astream(self, cmd: AnswerRequestDTO) -> AsyncIterable[AnswerStreamEventDTO]:
        """Process a question with streaming response asynchronously."""
        ...
