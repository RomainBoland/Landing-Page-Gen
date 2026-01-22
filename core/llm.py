"""LLM Client - OpenAI abstraction layer."""

import os
import re
from abc import ABC, abstractmethod
from typing import TypeVar, Type
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMClient(ABC):
    """Abstract interface for an LLM client."""

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Generate a text response."""
        pass

    def generate_structured(self, prompt: str, schema: Type[T]) -> T:
        """Generate a structured response according to a Pydantic schema."""
        response = self.generate(prompt)
        cleaned = self._extract_json(response)

        try:
            return schema.model_validate_json(cleaned)
        except Exception as e:
            print(f"      [DEBUG] Raw response: {response[:500]}...")
            print(f"      [DEBUG] Cleaned JSON: {cleaned[:500]}...")
            raise e

    def _extract_json(self, text: str) -> str:
        """Extract JSON from LLM response (handles markdown, surrounding text, etc.)."""
        text = text.strip()

        # Case 1: Markdown code block ```json ... ```
        if "```" in text:
            match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
            if match:
                return match.group(1).strip()

        # Case 2: Find first { and last }
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return text[start:end + 1]

        # Case 3: Find first [ and last ]
        start = text.find("[")
        end = text.rfind("]")
        if start != -1 and end != -1 and end > start:
            return text[start:end + 1]

        # Fallback: return as-is
        return text


class OpenAIClient(LLMClient):
    """OpenAI GPT client implementation."""

    def __init__(self, api_key: str | None = None, model: str = "gpt-4o"):
        try:
            import openai
        except ImportError:
            raise ImportError("Please install openai: pip install openai")

        self.client = openai.OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.model = model

    def generate(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content
