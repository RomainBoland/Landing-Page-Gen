"""Onboarding Agent - Transforms user input into structured project data."""

from core.schemas import UserInput, ProjectInfo
from core.llm import LLMClient
from .base import Agent


class OnboardingAgent(Agent):
    """
    Takes raw user input and generates an enriched ProjectInfo.
    Responsibilities:
    - Enrich product description
    - Generate a catchy tagline
    - Extract SEO keywords
    """

    name = "OnboardingAgent"

    PROMPT_TEMPLATE = """You are an expert SaaS copywriter and marketing specialist.

Based on the following product information, generate marketing data:

- Product: {product_name}
- Target audience: {target_audience}
- Value proposition: {value_proposition}
- Desired tone: {tone}
- Additional context: {additional_context}

Generate a JSON with EXACTLY this structure (replace values with your creations):

{{
  "product_name": "{product_name}",
  "tagline": "A catchy tagline of 6 words max",
  "description": "Enriched description of 2-3 sentences focused on user benefits",
  "target_audience": "{target_audience}",
  "value_proposition": "{value_proposition}",
  "tone": "{tone}",
  "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"]
}}

Respond ONLY with the JSON, no explanation."""

    def run(self, user_input: UserInput) -> ProjectInfo:
        """Transform UserInput into enriched ProjectInfo."""
        prompt = self.PROMPT_TEMPLATE.format(
            product_name=user_input.product_name,
            target_audience=user_input.target_audience,
            value_proposition=user_input.value_proposition,
            tone=user_input.tone,
            additional_context=user_input.additional_context or "None"
        )

        return self.llm.generate_structured(prompt, ProjectInfo)
