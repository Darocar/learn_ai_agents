"""Domain configuration models."""

from dataclasses import dataclass


@dataclass
class Config:
    """Configuration for agent interactions."""

    conversation_id: str
