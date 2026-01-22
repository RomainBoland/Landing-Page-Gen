"""Landing Agent - Generates content for the landing page.

Le LLM génère UNIQUEMENT du contenu textuel structuré (copy).
Le HTML est produit par le TemplateRenderer de manière déterministe.
"""

from core.schemas import CanonicalData, LandingContent, AssetSlots, SectionsConfig, ALLOWED_ICONS, TONE_PRESETS
from core.renderer import render_landing
from .base import Agent


class LandingAgent(Agent):
    """
    Génère le contenu textuel de la landing page.

    Responsabilités:
    - Créer le copy (hero, features, testimonial) via LLM
    - Appliquer les presets de ton au copy
    - Déléguer le rendu HTML au TemplateRenderer

    Le LLM ne génère JAMAIS de HTML directement.
    """

    name = "LandingAgent"

    # Liste d'icônes formatée pour le prompt
    _ICONS_LIST = ", ".join(sorted(ALLOWED_ICONS))

    CONTENT_PROMPT = """You are an expert landing page copywriter for SaaS products.

Create landing page content for:

- Product: {product_name}
- Tagline: {tagline}
- Description: {description}
- Value proposition: {value_proposition}
- Target audience: {target_audience}

TONE PRESET: {tone_name}
- Style: {tone_style}
- Copy rules: {tone_copy_rules}
- CTA style: {tone_cta_style}
{additional_tone_rules}

Available icons (use ONLY these): {icons_list}

Generate a JSON with EXACTLY this structure:

{{
  "hero": {{
    "headline": "Catchy and impactful headline (max 10 words)",
    "subheadline": "Explanatory subtitle of 1-2 sentences (max 200 chars)",
    "cta_text": "Call-to-action button text (2-4 words)"
  }},
  "features": [
    {{"title": "Feature 1 (2-4 words)", "description": "Benefit-focused description (max 100 chars)", "icon": "rocket"}},
    {{"title": "Feature 2", "description": "Short description", "icon": "shield"}},
    {{"title": "Feature 3", "description": "Short description", "icon": "zap"}}
  ],
  "testimonial": {{
    "quote": "Realistic fictional customer testimonial (1-2 sentences)",
    "author": "First Last",
    "role": "Position, Company Name"
  }},
  "footer_cta": "Final call-to-action phrase (max 10 words)",
  "variants": {{
    "headlines": [
      "Alternative headline 1 - different angle, same message",
      "Alternative headline 2 - more emotional/direct"
    ],
    "ctas": [
      "Alternative CTA 1 - more urgent",
      "Alternative CTA 2 - more benefit-focused"
    ]
  }},
  "faq_items": [
    {{"question": "Common question 1?", "answer": "Clear, helpful answer"}},
    {{"question": "Common question 2?", "answer": "Clear, helpful answer"}},
    {{"question": "Common question 3?", "answer": "Clear, helpful answer"}}
  ]
}}

IMPORTANT:
- Use icons ONLY from the provided list
- STRICTLY follow the {tone_name} tone preset guidelines
- Keep all text concise and benefit-focused
- Variants should offer genuinely different approaches, not just synonyms

Respond ONLY with the JSON, no explanation."""

    def run(self, data: CanonicalData) -> tuple[LandingContent, str]:
        """
        Génère le contenu puis rend le HTML.

        Args:
            data: Données canoniques avec project et brand

        Returns:
            Tuple (LandingContent, HTML string)
        """
        # 1. Génère le contenu textuel via LLM
        content = self._generate_content(data)

        # 2. Génère les asset prompts
        assets = self._generate_asset_prompts(data)
        data.assets = assets

        # 3. Injecte le contenu dans les données canoniques
        data.content = content

        # 4. Rend le HTML via le template Jinja2 (déterministe)
        html = render_landing(data)

        return content, html

    def _get_tone_preset(self, tone: str) -> dict[str, str]:
        """Récupère le preset de ton ou fallback sur professional."""
        return TONE_PRESETS.get(tone, TONE_PRESETS["professional"])

    def _generate_content(self, data: CanonicalData) -> LandingContent:
        """Génère le contenu textuel via LLM avec tone presets."""
        # Récupère le preset de ton
        tone_preset = self._get_tone_preset(data.project.tone)

        # Règles de ton additionnelles de la marque
        additional_rules = ""
        if data.brand and data.brand.tone_rules:
            additional_rules = f"\nAdditional brand tone rules: {', '.join(data.brand.tone_rules)}"

        prompt = self.CONTENT_PROMPT.format(
            product_name=data.project.product_name,
            tagline=data.project.tagline,
            description=data.project.description,
            value_proposition=data.project.value_proposition,
            target_audience=data.project.target_audience,
            tone_name=data.project.tone.upper(),
            tone_style=tone_preset["style"],
            tone_copy_rules=tone_preset["copy_rules"],
            tone_cta_style=tone_preset["cta_style"],
            additional_tone_rules=additional_rules,
            icons_list=self._ICONS_LIST,
        )

        content = self.llm.generate_structured(prompt, LandingContent)

        # Applique les sections par défaut selon le template
        content.sections = self._get_default_sections(data.render.template_type)

        return content

    def _get_default_sections(self, template_type: str) -> SectionsConfig:
        """Retourne les sections par défaut selon le type de template."""
        defaults = {
            "saas": SectionsConfig(feature_grid=True, faq=True, stats=False, logos=True),
            "app": SectionsConfig(feature_grid=True, faq=False, stats=True, screenshots=True),
            "agency": SectionsConfig(feature_grid=True, faq=False, stats=False, logos=False),
        }
        return defaults.get(template_type, SectionsConfig())

    def _generate_asset_prompts(self, data: CanonicalData) -> AssetSlots:
        """Génère les prompts pour les assets visuels (sans appel API image)."""
        product = data.project.product_name
        tone = data.project.tone

        # Mapping ton → style visuel
        visual_style = {
            "professional": "clean, corporate, trustworthy, blue tones",
            "friendly": "warm, colorful, welcoming, soft gradients",
            "bold": "high contrast, dynamic, striking, vibrant colors",
            "minimal": "simple, elegant, lots of whitespace, monochrome accents",
        }.get(tone, "modern and clean")

        return AssetSlots(
            hero_image_prompt=f"Modern {product} dashboard interface, {visual_style}, UI mockup, 16:9 aspect ratio",
            hero_image_alt=f"{product} application interface preview",
            og_image_prompt=f"{product} logo on gradient background, {visual_style}, social media card, 1200x630",
            screenshot_prompts=[
                f"{product} main dashboard view, {visual_style}",
                f"{product} feature highlight, {visual_style}",
            ],
        )
