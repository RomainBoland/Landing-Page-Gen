"""Moteur de rendu Jinja2 pour les templates HTML.

Ce module découple complètement la génération HTML des agents.
Le LLM ne génère jamais de HTML - il produit uniquement des données structurées
qui sont ensuite injectées dans des templates déterministes.

RÈGLES DE RENDU (v1.2.1)
========================

1. RÉSOLUTION DES VARIANTES (headline/CTA)
------------------------------------------
La valeur affichée dépend de variant_id:

    variant_id=0 → Utilise les valeurs par défaut:
        - headline = content.hero.headline
        - cta_text = content.hero.cta_text

    variant_id=N (N>0) → Utilise les variantes si disponibles:
        - headline = content.variants.headlines[N-1] (si existe)
        - cta_text = content.variants.ctas[N-1] (si existe)
        - Fallback vers défaut si index hors bornes

    Exemple:
        variant_id=1 → headlines[0], ctas[0]
        variant_id=2 → headlines[1], ctas[1]

2. SÉLECTION DU TEMPLATE
------------------------
Priorité:
    1. template_override (argument de render_landing)
    2. data.render.template_type
    3. Fallback: "saas"

Templates disponibles: saas, app, agency

3. COMPORTEMENT DES SECTIONS
----------------------------
Chaque section dans content.sections contrôle l'affichage:

    sections.feature_grid=True  → Affiche les features
    sections.feature_grid=False → Section masquée (non rendue)

    Si section activée MAIS données absentes:
        → Affiche un placeholder visuel (skeleton)

    Sections disponibles:
        - feature_grid (défaut: True)
        - stats (défaut: True)
        - pricing (défaut: False)
        - faq (défaut: False)
        - logos (défaut: False)
        - screenshots (défaut: False)

4. TONE STYLING
---------------
Le tone (professional/friendly/bold/minimal) affecte les classes CSS:

    professional → text-5xl md:text-6xl, rounded-lg
    friendly     → text-4xl md:text-5xl, rounded-full
    bold         → text-6xl md:text-7xl font-black, rounded-none uppercase
    minimal      → text-4xl md:text-5xl font-light, rounded-sm border

5. DÉTERMINISME
---------------
Le rendu est 100% déterministe:
    - Mêmes données → même HTML (sauf current_year)
    - Pas de randomisation
    - Pas de side effects
"""

from pathlib import Path
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape, TemplateNotFound

from core.schemas import CanonicalData, DefaultBrand, TemplateType, AssetSlots, SectionsConfig
from core.errors import RenderError, ErrorCode
from core.logging_config import get_logger

logger = get_logger(__name__)

# ==============================================================================
# CONSTANTES
# ==============================================================================

# Chemin vers le dossier templates
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"

# Mapping icônes vers symboles Unicode
ICON_MAP: dict[str, str] = {
    "rocket": "🚀",
    "shield": "🛡️",
    "zap": "⚡",
    "star": "⭐",
    "heart": "❤️",
    "check": "✓",
    "lightning": "⚡",
    "chart": "📊",
    "users": "👥",
    "clock": "⏰",
    "lock": "🔒",
    "globe": "🌐",
    "mail": "✉️",
    "phone": "📱",
    "settings": "⚙️",
    "layers": "📚",
    "target": "🎯",
    "trending": "📈",
    "award": "🏆",
    "briefcase": "💼",
}

# Icône par défaut si non trouvée
DEFAULT_ICON = "✦"

# Mapping template_type -> fichier template
TEMPLATE_FILES: dict[TemplateType, str] = {
    "saas": "saas.html.j2",
    "app": "app.html.j2",
    "agency": "agency.html.j2",
}

# Mapping tone → classes CSS Tailwind
TONE_STYLES: dict[str, dict[str, str]] = {
    "professional": {
        "hero_size": "text-5xl md:text-6xl",
        "cta_style": "rounded-lg",
    },
    "friendly": {
        "hero_size": "text-4xl md:text-5xl",
        "cta_style": "rounded-full",
    },
    "bold": {
        "hero_size": "text-6xl md:text-7xl font-black",
        "cta_style": "rounded-none uppercase tracking-wider",
    },
    "minimal": {
        "hero_size": "text-4xl md:text-5xl font-light",
        "cta_style": "rounded-sm border",
    },
}


# ==============================================================================
# RENDERER CLASS
# ==============================================================================

class TemplateRenderer:
    """Moteur de rendu pour les landing pages.

    Responsabilités:
    - Charger les templates Jinja2
    - Injecter les données canoniques
    - Produire du HTML déterministe

    Usage:
        renderer = TemplateRenderer()
        html = renderer.render_landing(canonical_data)
    """

    def __init__(self, templates_dir: Path | None = None):
        """Initialise le renderer avec le dossier de templates.

        Args:
            templates_dir: Chemin vers les templates (défaut: ./templates)
        """
        self.templates_dir = templates_dir or TEMPLATES_DIR
        self.env = Environment(
            loader=FileSystemLoader(self.templates_dir),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        logger.debug(f"TemplateRenderer initialized with templates_dir={self.templates_dir}")

    def render_landing(
        self,
        data: CanonicalData,
        template_override: TemplateType | None = None,
        variant_override: int | None = None,
    ) -> str:
        """Rend une landing page complète depuis les données canoniques.

        Règles de résolution:
        - Template: template_override > data.render.template_type > "saas"
        - Variant: variant_override > data.render.variant_id > 0
        - Si variant_id hors bornes: fallback vers défaut (0)

        Args:
            data: Données canoniques avec project, brand, et content
            template_override: Force un type de template
            variant_override: Force une variante

        Returns:
            HTML complet de la landing page

        Raises:
            RenderError: Si content est None ou template introuvable
        """
        # Validation: content requis
        if data.content is None:
            raise RenderError(
                message="CanonicalData.content is required for rendering",
                code=ErrorCode.MISSING_CONTENT,
            )

        # Résolution du template
        template_type = template_override or data.render.template_type
        template_file = TEMPLATE_FILES.get(template_type, "saas.html.j2")

        try:
            template = self.env.get_template(template_file)
        except TemplateNotFound:
            raise RenderError(
                message=f"Template '{template_file}' not found",
                template=template_file,
                code=ErrorCode.TEMPLATE_NOT_FOUND,
            )

        # Résolution de la variante (avec clamp si hors bornes)
        variant_id = variant_override if variant_override is not None else data.render.variant_id
        effective_variant_id = self._clamp_variant_id(variant_id, data.content.variants)

        if effective_variant_id != variant_id:
            logger.warning(
                f"variant_id={variant_id} out of bounds, clamped to {effective_variant_id}"
            )

        # Résolution headline/CTA selon variante
        headline = self._resolve_variant(
            default=data.content.hero.headline,
            variants=data.content.variants.headlines,
            variant_id=effective_variant_id,
        )
        cta_text = self._resolve_variant(
            default=data.content.hero.cta_text,
            variants=data.content.variants.ctas,
            variant_id=effective_variant_id,
        )

        # Brand avec fallback explicite
        brand = data.brand or DefaultBrand.IDENTITY
        if data.brand is None:
            logger.info("Using DefaultBrand (no brand data provided)")

        # Sections et Assets avec fallback
        sections = data.content.sections or SectionsConfig()
        assets = data.assets or AssetSlots()

        # Style selon le tone
        tone_style = TONE_STYLES.get(data.project.tone, TONE_STYLES["professional"])

        logger.debug(
            f"Rendering: template={template_type}, variant={effective_variant_id}, "
            f"tone={data.project.tone}, sections={sections.enabled_sections()}"
        )

        # Rendu du template
        return template.render(
            project=data.project,
            brand=brand,
            content=data.content,
            headline=headline,
            cta_text=cta_text,
            icons=ICON_MAP,
            default_icon=DEFAULT_ICON,
            current_year=datetime.now().year,
            sections=sections,
            assets=assets,
            tone=data.project.tone,
            tone_style=tone_style,
        )

    def _resolve_variant(
        self,
        default: str,
        variants: list[str],
        variant_id: int,
    ) -> str:
        """Résout la valeur selon la variante demandée.

        Règle:
            variant_id=0 → default
            variant_id=N → variants[N-1] si existe, sinon default

        Args:
            default: Valeur par défaut (hero.headline ou hero.cta_text)
            variants: Liste des variantes alternatives
            variant_id: Index de la variante (0=défaut)

        Returns:
            La valeur résolue
        """
        if variant_id == 0 or not variants:
            return default

        # variant_id 1 → variants[0], variant_id 2 → variants[1], etc.
        idx = variant_id - 1
        if 0 <= idx < len(variants):
            return variants[idx]

        # Hors bornes: fallback vers défaut
        return default

    def _clamp_variant_id(self, variant_id: int, variants) -> int:
        """Clamp le variant_id aux bornes valides.

        Args:
            variant_id: ID demandé
            variants: ContentVariants avec headlines/ctas

        Returns:
            variant_id si valide, 0 sinon
        """
        if variant_id == 0:
            return 0

        max_variant = variants.max_variant_id() if variants else 0
        if variant_id > max_variant:
            return 0  # Fallback vers défaut

        return variant_id


# ==============================================================================
# SINGLETON ET FONCTIONS HELPER
# ==============================================================================

_renderer: TemplateRenderer | None = None


def get_renderer() -> TemplateRenderer:
    """Retourne l'instance singleton du renderer."""
    global _renderer
    if _renderer is None:
        _renderer = TemplateRenderer()
    return _renderer


def render_landing(
    data: CanonicalData,
    template_override: TemplateType | None = None,
    variant_override: int | None = None,
) -> str:
    """Raccourci pour rendre une landing page.

    Voir TemplateRenderer.render_landing() pour la documentation complète.
    """
    return get_renderer().render_landing(data, template_override, variant_override)


def render_all_variants(data: CanonicalData) -> dict[str, str]:
    """Génère toutes les combinaisons template × variante.

    Itère sur tous les templates (saas, app, agency) et toutes les variantes
    disponibles (0 à N où N = len(variants.headlines)).

    Args:
        data: Données canoniques complètes

    Returns:
        Dict avec clés "{template_type}_v{variant_id}" → HTML

    Example:
        {
            "saas_v0": "<html>...",
            "saas_v1": "<html>...",
            "app_v0": "<html>...",
            "app_v1": "<html>...",
            "agency_v0": "<html>...",
            "agency_v1": "<html>...",
        }
    """
    renderer = get_renderer()
    results = {}

    # Nombre de variantes disponibles
    num_variants = 0
    if data.content and data.content.variants.headlines:
        num_variants = len(data.content.variants.headlines)

    logger.info(
        f"Rendering all variants: {len(TEMPLATE_FILES)} templates × {num_variants + 1} variants"
    )

    for template_type in TEMPLATE_FILES.keys():
        # Variante 0 (défaut) - toujours générée
        key = f"{template_type}_v0"
        results[key] = renderer.render_landing(data, template_type, 0)
        logger.debug(f"Rendered: {key}")

        # Variantes alternatives (si disponibles)
        for i in range(1, num_variants + 1):
            key = f"{template_type}_v{i}"
            results[key] = renderer.render_landing(data, template_type, i)
            logger.debug(f"Rendered: {key}")

    logger.info(f"Total rendered: {len(results)} files")
    return results
