"""Brand Agent - Generates visual identity from project data."""

from core.schemas import ProjectInfo, BrandIdentity
from .base import Agent


class BrandAgent(Agent):
    """
    Generates brand identity based on ProjectInfo.
    Responsibilities:
    - Coherent color palette
    - Typography choices
    - Editorial tone rules
    """

    name = "BrandAgent"

    PROMPT_TEMPLATE = """You are an expert UI/UX designer and branding specialist.

Create a brand identity for this product:

- Product: {product_name}
- Tagline: {tagline}
- Audience: {target_audience}
- Tone: {tone} (friendly=warm, professional=corporate, bold=daring, minimal=clean)

Generate a JSON with EXACTLY this structure:

{{
  "colors": {{
    "primary": "#HEX main brand color",
    "secondary": "#HEX secondary color",
    "accent": "#HEX accent/CTA color",
    "background": "#HEX light background",
    "text": "#HEX dark text color"
  }},
  "fonts": {{
    "heading": "Google Font name for headings",
    "body": "Google Font name for body text"
  }},
  "tone_rules": [
    "Tone rule 1",
    "Tone rule 2",
    "Tone rule 3"
  ]
}}

Respond ONLY with the JSON, no explanation."""

    def run(self, project: ProjectInfo) -> BrandIdentity:
        """Generate BrandIdentity from ProjectInfo."""
        prompt = self.PROMPT_TEMPLATE.format(
            product_name=project.product_name,
            tagline=project.tagline,
            description=project.description,
            target_audience=project.target_audience,
            tone=project.tone
        )

        return self.llm.generate_structured(prompt, BrandIdentity)
