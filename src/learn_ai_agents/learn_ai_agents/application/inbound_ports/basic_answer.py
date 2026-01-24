"""Inbound port for basic answer functionality."""

from collections.abc import Iterable
from typing import Protocol

from ..dtos.basic_answer import AnswerRequestDTO, AnswerResultDTO, AnswerStreamEventDTO


class BasicAnswerPort(Protocol):
    """Inbound port for basic question-answering functionality."""

    def invoke(self, cmd: AnswerRequestDTO) -> AnswerResultDTO:
        """Process a question and return the answer."""
        ...

    def stream(self, cmd: AnswerRequestDTO) -> Iterable[AnswerStreamEventDTO]:
        """Process a question with streaming response."""
        ...
