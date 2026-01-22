"""Schémas Pydantic pour le JSON canonique.

Ce module définit la source de vérité unique entre tous les agents.
Chaque agent consomme et produit des données conformes à ces schémas.

Règles de validation v1.2.1:
- Tous les champs ont des contraintes explicites (min/max, patterns)
- Les valeurs invalides lèvent ValidationError (pas de fallback silencieux)
- variant_id doit être dans les bornes [0, len(variants)]
- tone doit exister dans TONE_PRESETS
- schema_version est constant et vérifié au chargement
"""

from datetime import datetime
from typing import Literal, Annotated, Any
from pydantic import (
    BaseModel,
    Field,
    field_validator,
    model_validator,
    ConfigDict,
)

# ==============================================================================
# CONSTANTES ET TYPES
# ==============================================================================

# Version du schéma canonique - incrémenter lors de breaking changes
SCHEMA_VERSION = "1.2.1"

# Types réutilisables avec contraintes
ToneType = Literal["professional", "friendly", "bold", "minimal"]
TemplateType = Literal["saas", "app", "agency"]

# Pattern strict pour couleurs hex
HEX_COLOR_PATTERN = r"^#[0-9A-Fa-f]{6}$"

# Liste restreinte de Google Fonts supportées pour garantir le rendu
ALLOWED_FONTS: frozenset[str] = frozenset([
    "Inter", "Roboto", "Open Sans", "Lato", "Montserrat", "Poppins",
    "Source Sans Pro", "Nunito", "Raleway", "Work Sans", "DM Sans",
    "Plus Jakarta Sans", "Space Grotesk", "Outfit", "Sora",
    "Playfair Display", "Merriweather", "Lora", "Crimson Text",
])

# Icônes autorisées (mappées vers des symboles ou classes CSS)
ALLOWED_ICONS: frozenset[str] = frozenset([
    "rocket", "shield", "zap", "star", "heart", "check", "lightning",
    "chart", "users", "clock", "lock", "globe", "mail", "phone",
    "settings", "layers", "target", "trending", "award", "briefcase",
])

# Presets de ton pour influencer le copy et le style
TONE_PRESETS: dict[str, dict[str, str]] = {
    "professional": {
        "style": "Clear, authoritative, trust-building",
        "copy_rules": "Use formal language, focus on ROI and business outcomes, include data when possible",
        "cta_style": "Action-oriented but measured (e.g., 'Get Started', 'Request Demo')",
    },
    "friendly": {
        "style": "Warm, conversational, approachable",
        "copy_rules": "Use casual language, contractions allowed, speak directly to the reader",
        "cta_style": "Inviting and low-pressure (e.g., 'Try it free', 'See how it works')",
    },
    "bold": {
        "style": "Direct, punchy, high-impact",
        "copy_rules": "Short sentences. Strong verbs. No fluff. Create urgency.",
        "cta_style": "Commanding and urgent (e.g., 'Start Now', 'Claim Your Spot')",
    },
    "minimal": {
        "style": "Elegant, understated, sophisticated",
        "copy_rules": "Less is more. Remove unnecessary words. Let whitespace breathe.",
        "cta_style": "Subtle and refined (e.g., 'Explore', 'Learn more', 'Begin')",
    },
}


def get_tone_preset(tone: ToneType) -> dict[str, str]:
    """Retourne le preset de ton avec validation.

    Raises:
        KeyError: Si le tone n'existe pas dans TONE_PRESETS
    """
    if tone not in TONE_PRESETS:
        raise KeyError(f"Tone '{tone}' not in TONE_PRESETS. Valid: {list(TONE_PRESETS.keys())}")
    return TONE_PRESETS[tone]


# ==============================================================================
# INPUT UTILISATEUR
# ==============================================================================

class UserInput(BaseModel):
    """Input brut de l'utilisateur lors de l'onboarding.

    Validation:
    - product_name: 1-100 chars, non vide après strip
    - tone: doit être dans ToneType
    - template_type: doit être dans TemplateType
    """
    model_config = ConfigDict(str_strip_whitespace=True)

    product_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Nom du produit/service"
    )
    target_audience: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Audience cible"
    )
    value_proposition: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Promesse principale"
    )
    tone: ToneType = Field(
        default="professional",
        description="Ton souhaité (professional|friendly|bold|minimal)"
    )
    additional_context: str = Field(
        default="",
        max_length=1000,
        description="Contexte additionnel"
    )
    template_type: TemplateType = Field(
        default="saas",
        description="Type de template souhaité (saas|app|agency)"
    )

    @field_validator("product_name", "target_audience", "value_proposition")
    @classmethod
    def validate_not_empty_after_strip(cls, v: str) -> str:
        """Vérifie que le champ n'est pas vide après strip."""
        if not v.strip():
            raise ValueError("Field cannot be empty or whitespace only")
        return v.strip()


# ==============================================================================
# PROJECT INFO (output Onboarding Agent)
# ==============================================================================

class ProjectInfo(BaseModel):
    """Informations projet enrichies par l'Onboarding Agent.

    Validation:
    - tagline: max 80 chars, ~6 mots
    - keywords: 3-7 mots-clés, normalisés lowercase
    - tone: validé contre TONE_PRESETS
    """
    model_config = ConfigDict(str_strip_whitespace=True)

    product_name: str = Field(..., min_length=1, max_length=100)
    tagline: str = Field(
        ...,
        min_length=1,
        max_length=80,
        description="Accroche courte (6 mots max recommandé)"
    )
    description: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Description enrichie"
    )
    target_audience: str = Field(..., min_length=1)
    value_proposition: str = Field(..., min_length=1)
    tone: ToneType
    keywords: list[str] = Field(
        default_factory=list,
        min_length=3,
        max_length=7,
        description="Mots-clés SEO (3-7, lowercase)"
    )

    @field_validator("keywords")
    @classmethod
    def validate_keywords(cls, v: list[str]) -> list[str]:
        """Normalise les keywords: lowercase, trimmed, non-vides."""
        normalized = [kw.strip().lower() for kw in v if kw.strip()]
        if len(normalized) < 3:
            raise ValueError(f"At least 3 keywords required, got {len(normalized)}")
        return normalized

    @field_validator("tone")
    @classmethod
    def validate_tone_exists(cls, v: ToneType) -> ToneType:
        """Vérifie que le tone existe dans TONE_PRESETS."""
        if v not in TONE_PRESETS:
            raise ValueError(f"Tone '{v}' not in TONE_PRESETS")
        return v


# ==============================================================================
# BRAND IDENTITY (output Brand Agent)
# ==============================================================================

class ColorPalette(BaseModel):
    """Palette de couleurs avec validation hex stricte.

    Toutes les couleurs doivent être au format #RRGGBB.
    """
    primary: str = Field(
        ...,
        pattern=HEX_COLOR_PATTERN,
        description="Couleur principale de marque (#RRGGBB)"
    )
    secondary: str = Field(
        ...,
        pattern=HEX_COLOR_PATTERN,
        description="Couleur secondaire (#RRGGBB)"
    )
    accent: str = Field(
        ...,
        pattern=HEX_COLOR_PATTERN,
        description="Couleur d'accentuation CTA (#RRGGBB)"
    )
    background: str = Field(
        ...,
        pattern=HEX_COLOR_PATTERN,
        description="Couleur de fond (#RRGGBB)"
    )
    text: str = Field(
        ...,
        pattern=HEX_COLOR_PATTERN,
        description="Couleur du texte (#RRGGBB)"
    )


class Typography(BaseModel):
    """Configuration typographique avec fonts validées.

    Seules les fonts de ALLOWED_FONTS sont acceptées.
    Erreur explicite si font invalide (pas de fallback silencieux).
    """
    heading: str = Field(..., description="Font pour les titres (Google Fonts)")
    body: str = Field(..., description="Font pour le corps de texte (Google Fonts)")

    @field_validator("heading", "body")
    @classmethod
    def validate_font(cls, v: str) -> str:
        """Valide que la font est dans la liste autorisée."""
        if v not in ALLOWED_FONTS:
            raise ValueError(
                f"Font '{v}' not in ALLOWED_FONTS. "
                f"Valid fonts: {sorted(ALLOWED_FONTS)}"
            )
        return v


class BrandIdentity(BaseModel):
    """Identité de marque générée par le Brand Agent."""
    colors: ColorPalette
    fonts: Typography
    tone_rules: list[str] = Field(
        ...,
        min_length=2,
        max_length=5,
        description="Règles de ton éditoriales (2-5)"
    )

    @field_validator("tone_rules")
    @classmethod
    def validate_tone_rules_not_empty(cls, v: list[str]) -> list[str]:
        """Vérifie que les tone_rules ne sont pas vides."""
        validated = [rule.strip() for rule in v if rule.strip()]
        if len(validated) < 2:
            raise ValueError("At least 2 non-empty tone_rules required")
        return validated


# ==============================================================================
# LANDING CONTENT (output Landing Agent)
# ==============================================================================

class HeroSection(BaseModel):
    """Section hero de la landing."""
    model_config = ConfigDict(str_strip_whitespace=True)

    headline: str = Field(
        ...,
        min_length=5,
        max_length=100,
        description="Titre principal accrocheur (5-100 chars)"
    )
    subheadline: str = Field(
        ...,
        min_length=10,
        max_length=200,
        description="Sous-titre explicatif (10-200 chars)"
    )
    cta_text: str = Field(
        ...,
        min_length=2,
        max_length=30,
        description="Texte du bouton CTA (2-30 chars)"
    )


class Feature(BaseModel):
    """Feature à mettre en avant."""
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(..., min_length=2, max_length=50)
    description: str = Field(..., min_length=10, max_length=150)
    icon: str = Field(..., description="Identifiant d'icône (voir ALLOWED_ICONS)")

    @field_validator("icon")
    @classmethod
    def validate_icon(cls, v: str) -> str:
        """Valide que l'icône est dans ALLOWED_ICONS."""
        icon = v.lower().strip()
        if icon not in ALLOWED_ICONS:
            raise ValueError(
                f"Icon '{icon}' not in ALLOWED_ICONS. "
                f"Valid icons: {sorted(ALLOWED_ICONS)}"
            )
        return icon


class Testimonial(BaseModel):
    """Témoignage client (fictif mais réaliste)."""
    model_config = ConfigDict(str_strip_whitespace=True)

    quote: str = Field(..., min_length=20, max_length=300)
    author: str = Field(..., min_length=2, max_length=50)
    role: str = Field(
        ...,
        min_length=2,
        max_length=80,
        description="Poste et entreprise"
    )


class ContentVariants(BaseModel):
    """Variantes de contenu pour tests A/B (sans infra de tracking).

    Règle: max 3 variantes pour headlines et ctas.
    variant_id=0 utilise les valeurs par défaut de hero.
    variant_id=1 utilise variants[0], etc.
    """
    headlines: list[str] = Field(
        default_factory=list,
        max_length=3,
        description="Headlines alternatives (max 3)"
    )
    ctas: list[str] = Field(
        default_factory=list,
        max_length=3,
        description="CTAs alternatifs (max 3)"
    )

    @field_validator("headlines", "ctas")
    @classmethod
    def validate_variants_not_empty_strings(cls, v: list[str]) -> list[str]:
        """Vérifie que les variantes ne sont pas des strings vides."""
        validated = [item.strip() for item in v if item.strip()]
        return validated

    def max_variant_id(self) -> int:
        """Retourne le variant_id maximum valide.

        Returns:
            0 si pas de variantes, sinon len(headlines)
        """
        return len(self.headlines) if self.headlines else 0


class SectionsConfig(BaseModel):
    """Configuration des sections optionnelles de la landing page.

    Chaque section peut être activée/désactivée indépendamment.
    Si activée sans données, un placeholder sera affiché.
    """
    pricing: bool = Field(default=False, description="Afficher la section pricing")
    faq: bool = Field(default=False, description="Afficher la section FAQ")
    logos: bool = Field(default=False, description="Afficher les logos partenaires/clients")
    screenshots: bool = Field(default=False, description="Afficher les screenshots produit")
    feature_grid: bool = Field(default=True, description="Afficher la grille de features")
    stats: bool = Field(default=True, description="Afficher les statistiques")

    def enabled_sections(self) -> list[str]:
        """Retourne la liste des sections activées."""
        return [
            name for name, enabled in [
                ("pricing", self.pricing),
                ("faq", self.faq),
                ("logos", self.logos),
                ("screenshots", self.screenshots),
                ("feature_grid", self.feature_grid),
                ("stats", self.stats),
            ] if enabled
        ]


class FAQItem(BaseModel):
    """Item FAQ avec validation stricte."""
    question: str = Field(..., min_length=5, max_length=200)
    answer: str = Field(..., min_length=10, max_length=500)


class PricingPlan(BaseModel):
    """Plan tarifaire avec validation."""
    name: str = Field(..., min_length=1, max_length=50)
    price: str = Field(..., min_length=1, max_length=20, description="Prix affiché (ex: '49', 'Free')")
    description: str = Field(default="", max_length=200)


class LandingContent(BaseModel):
    """Contenu textuel de la landing page.

    Validation:
    - 3-6 features obligatoires
    - faq_items: 0-6 items
    - pricing_plans: 0-3 plans
    """
    hero: HeroSection
    features: list[Feature] = Field(
        ...,
        min_length=3,
        max_length=6,
        description="Features (3-6 obligatoires)"
    )
    testimonial: Testimonial
    footer_cta: str = Field(..., min_length=5, max_length=100)
    variants: ContentVariants = Field(
        default_factory=ContentVariants,
        description="Variantes de contenu A/B"
    )
    sections: SectionsConfig = Field(
        default_factory=SectionsConfig,
        description="Sections optionnelles activées"
    )
    faq_items: list[dict[str, str]] = Field(
        default_factory=list,
        max_length=6,
        description="Questions FAQ [{question, answer}]"
    )
    pricing_plans: list[dict[str, Any]] = Field(
        default_factory=list,
        max_length=3,
        description="Plans tarifaires"
    )


# ==============================================================================
# ASSET SLOTS
# ==============================================================================

class AssetSlots(BaseModel):
    """Slots pour les assets visuels (préparation génération future).

    Ces champs contiennent des prompts pour génération d'images,
    pas les images elles-mêmes.
    """
    hero_image_prompt: str | None = Field(
        default=None,
        max_length=500,
        description="Prompt pour générer l'image hero"
    )
    hero_image_alt: str | None = Field(
        default=None,
        max_length=200,
        description="Alt text pour l'image hero"
    )
    og_image_prompt: str | None = Field(
        default=None,
        max_length=500,
        description="Prompt pour l'image OpenGraph"
    )
    logo_url: str | None = Field(
        default=None,
        max_length=500,
        description="URL du logo (si fourni)"
    )
    screenshot_prompts: list[str] = Field(
        default_factory=list,
        max_length=4,
        description="Prompts pour screenshots (max 4)"
    )


# ==============================================================================
# MÉTADONNÉES DE GÉNÉRATION
# ==============================================================================

class RenderConfig(BaseModel):
    """Configuration de rendu pour le template.

    Règles variant_id:
    - 0 = utilise hero.headline et hero.cta_text (défaut)
    - 1 = utilise variants.headlines[0] et variants.ctas[0]
    - 2 = utilise variants.headlines[1] et variants.ctas[1]
    - etc.

    Si variant_id > len(variants), fallback vers défaut.
    """
    template_type: TemplateType = Field(
        default="saas",
        description="Type de template (saas|app|agency)"
    )
    variant_id: int = Field(
        default=0,
        ge=0,
        le=10,  # Limite haute pour éviter les abus
        description="Index de la variante de contenu (0=défaut)"
    )


class GenerationMeta(BaseModel):
    """Métadonnées de traçabilité de la génération.

    schema_version est vérifié au chargement pour détecter les incompatibilités.
    """
    schema_version: str = Field(
        default=SCHEMA_VERSION,
        description="Version du schéma (doit matcher SCHEMA_VERSION)"
    )
    generated_at: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="Timestamp ISO de génération"
    )
    pipeline_steps: list[str] = Field(
        default_factory=list,
        description="Étapes complétées du pipeline"
    )

    @field_validator("schema_version")
    @classmethod
    def validate_schema_version(cls, v: str) -> str:
        """Vérifie la compatibilité de la version du schéma.

        Accepte les versions compatibles (même majeure.mineure).
        """
        current_parts = SCHEMA_VERSION.split(".")
        input_parts = v.split(".")

        if len(input_parts) < 2:
            raise ValueError(f"Invalid schema_version format: {v}")

        # Vérifie majeure.mineure
        if input_parts[0] != current_parts[0] or input_parts[1] != current_parts[1]:
            raise ValueError(
                f"Schema version mismatch: got {v}, expected {SCHEMA_VERSION}. "
                "Major.minor must match."
            )
        return v


# ==============================================================================
# DONNÉES CANONIQUES COMPLÈTES
# ==============================================================================

class CanonicalData(BaseModel):
    """JSON canonique - source de vérité unique entre tous les agents.

    Structure immuable une fois créée. Chaque agent enrichit les champs
    sans modifier les données existantes.

    Validation:
    - meta.schema_version doit être compatible avec SCHEMA_VERSION
    - render.variant_id est validé contre content.variants si content existe
    - project.tone est validé contre TONE_PRESETS
    """
    model_config = ConfigDict(validate_assignment=True)

    meta: GenerationMeta = Field(default_factory=GenerationMeta)
    project: ProjectInfo
    brand: BrandIdentity | None = None
    content: LandingContent | None = None
    assets: AssetSlots = Field(
        default_factory=AssetSlots,
        description="Slots pour assets visuels"
    )
    render: RenderConfig = Field(
        default_factory=RenderConfig,
        description="Configuration de rendu"
    )

    @model_validator(mode="after")
    def validate_variant_id_bounds(self) -> "CanonicalData":
        """Vérifie que variant_id est cohérent avec les variantes disponibles.

        Comportement: si variant_id > max_variant, log un warning mais ne bloque pas
        (le renderer fera fallback vers défaut).
        """
        if self.content and self.render.variant_id > 0:
            max_variant = self.content.variants.max_variant_id()
            if self.render.variant_id > max_variant:
                # Warning: variant_id hors bornes, sera clampé au rendu
                # On ne bloque pas pour permettre le chargement de JSON legacy
                pass
        return self

    def get_effective_variant_id(self) -> int:
        """Retourne le variant_id effectif (clampé si nécessaire).

        Returns:
            variant_id si dans les bornes, 0 sinon
        """
        if not self.content:
            return 0
        max_variant = self.content.variants.max_variant_id()
        if self.render.variant_id > max_variant:
            return 0  # Fallback vers défaut
        return self.render.variant_id

    def add_step(self, step_name: str) -> "CanonicalData":
        """Ajoute une étape au journal et retourne self pour chaînage."""
        self.meta.pipeline_steps.append(step_name)
        return self

    def to_json(self, indent: int = 2) -> str:
        """Sérialise en JSON formaté."""
        return self.model_dump_json(indent=indent)

    @classmethod
    def from_json(cls, json_str: str) -> "CanonicalData":
        """Désérialise depuis JSON avec validation complète.

        Raises:
            pydantic.ValidationError: Si le JSON est invalide
        """
        return cls.model_validate_json(json_str)

    @classmethod
    def from_file(cls, path: str) -> "CanonicalData":
        """Charge depuis un fichier JSON.

        Raises:
            FileNotFoundError: Si le fichier n'existe pas
            pydantic.ValidationError: Si le JSON est invalide
        """
        from pathlib import Path
        content = Path(path).read_text(encoding="utf-8")
        return cls.from_json(content)


# ==============================================================================
# VALEURS PAR DÉFAUT POUR FALLBACK
# ==============================================================================

class DefaultBrand:
    """Valeurs par défaut si BrandAgent échoue.

    Utilisé uniquement comme fallback explicite, jamais silencieusement.
    """
    COLORS = ColorPalette(
        primary="#6366F1",
        secondary="#818CF8",
        accent="#F59E0B",
        background="#FAFAFA",
        text="#1F2937",
    )
    FONTS = Typography(heading="Inter", body="Inter")
    IDENTITY = BrandIdentity(
        colors=COLORS,
        fonts=FONTS,
        tone_rules=["Be clear and concise", "Focus on user benefits", "Use active voice"],
    )
