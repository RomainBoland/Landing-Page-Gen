"""Base Agent - defines the common contract for all agents."""

from abc import ABC, abstractmethod
from typing import Any

from core.llm import LLMClient


class Agent(ABC):
    """Abstract base class for all agents."""

    name: str = "BaseAgent"

    def __init__(self, llm: LLMClient):
        self.llm = llm

    @abstractmethod
    def run(self, input_data: Any) -> Any:
        """Execute the agent's logic."""
        pass

    def __repr__(self) -> str:
        return f"<{self.name}>"
