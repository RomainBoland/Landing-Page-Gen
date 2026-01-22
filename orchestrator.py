"""Orchestrator - Pipeline de génération de landing pages.

Ce module orchestre les agents de manière séquentielle.
Le JSON canonique est la source de vérité unique entre les agents.
"""

from dataclasses import dataclass, field
from pathlib import Path

from core.llm import LLMClient
from core.schemas import UserInput, CanonicalData, DefaultBrand, RenderConfig, TemplateType
from core.renderer import render_landing, render_all_variants
from agents import OnboardingAgent, BrandAgent, LandingAgent


@dataclass
class PipelineResult:
    """Résultat complet du pipeline."""
    canonical_data: CanonicalData | None
    html: str
    success: bool
    errors: list[str] = field(default_factory=list)

    def save(self, output_dir: str | Path, save_all_variants: bool = False) -> dict[str, Path]:
        """
        Sauvegarde les outputs dans un dossier.

        Args:
            output_dir: Dossier de destination
            save_all_variants: Si True, génère toutes les combinaisons template × variante

        Returns:
            Dict avec les chemins des fichiers créés
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        paths: dict[str, Path] = {}

        # Sauvegarde le JSON canonique
        if self.canonical_data:
            json_path = output_dir / "canonical.json"
            json_path.write_text(self.canonical_data.to_json(), encoding="utf-8")
            paths["json"] = json_path

        # Sauvegarde le HTML principal
        if self.html:
            html_path = output_dir / "index.html"
            html_path.write_text(self.html, encoding="utf-8")
            paths["html"] = html_path

        # Sauvegarde toutes les variantes si demandé
        if save_all_variants and self.canonical_data:
            variants_dir = output_dir / "variants"
            variants_dir.mkdir(exist_ok=True)
            all_variants = render_all_variants(self.canonical_data)
            for variant_key, variant_html in all_variants.items():
                variant_path = variants_dir / f"{variant_key}.html"
                variant_path.write_text(variant_html, encoding="utf-8")
                paths[f"variant_{variant_key}"] = variant_path

        return paths


class LandingPipeline:
    """
    Orchestrateur du pipeline de génération.

    Flow:
    UserInput → OnboardingAgent → ProjectInfo
                               → BrandAgent → BrandIdentity
                                           → LandingAgent → HTML

    Le JSON canonique (CanonicalData) est enrichi à chaque étape.
    """

    def __init__(self, llm: LLMClient):
        self.llm = llm
        self.onboarding = OnboardingAgent(llm)
        self.brand = BrandAgent(llm)
        self.landing = LandingAgent(llm)

    def run(
        self,
        user_input: UserInput,
        output_dir: str | None = None,
    ) -> PipelineResult:
        """
        Exécute le pipeline complet.

        Args:
            user_input: Input utilisateur initial
            output_dir: Dossier optionnel pour sauvegarder les outputs

        Returns:
            PipelineResult avec toutes les données générées
        """
        errors: list[str] = []

        # === Étape 1: Onboarding - Enrichir l'input ===
        print(f"[1/3] {self.onboarding.name} - Enriching project... (template: {user_input.template_type})")
        try:
            project_info = self.onboarding.run(user_input)
            print(f"      ✓ Tagline: {project_info.tagline}")
        except Exception as e:
            errors.append(f"OnboardingAgent failed: {e}")
            return PipelineResult(
                canonical_data=None,
                html="",
                success=False,
                errors=errors,
            )

        # Initialise le JSON canonique avec la config de rendu
        render_config = RenderConfig(template_type=user_input.template_type)
        canonical = CanonicalData(project=project_info, render=render_config)
        canonical.add_step("onboarding")

        # === Étape 2: Brand - Générer l'identité visuelle ===
        print(f"[2/3] {self.brand.name} - Generating identity...")
        try:
            brand_identity = self.brand.run(project_info)
            canonical.brand = brand_identity
            canonical.add_step("brand")
            print(f"      ✓ Palette: {brand_identity.colors.primary} (primary)")
        except Exception as e:
            # Fallback vers les valeurs par défaut
            errors.append(f"BrandAgent failed (using defaults): {e}")
            canonical.brand = DefaultBrand.IDENTITY
            canonical.add_step("brand:fallback")
            print(f"      ⚠ Using default brand (error: {e})")

        # === Étape 3: Landing - Générer contenu et HTML ===
        print(f"[3/3] {self.landing.name} - Generating landing page...")
        try:
            content, html = self.landing.run(canonical)
            canonical.content = content
            canonical.add_step("landing")
            print(f"      ✓ Hero: {content.hero.headline[:50]}...")
            if content.variants.headlines:
                print(f"      ✓ Variants: {len(content.variants.headlines)} headlines, {len(content.variants.ctas)} CTAs")
        except Exception as e:
            errors.append(f"LandingAgent failed: {e}")
            return PipelineResult(
                canonical_data=canonical,
                html="",
                success=False,
                errors=errors,
            )

        # Crée le résultat
        result = PipelineResult(
            canonical_data=canonical,
            html=html,
            success=len(errors) == 0,
            errors=errors,
        )

        # Sauvegarde optionnelle
        if output_dir:
            paths = result.save(output_dir)
            print(f"\n✓ Output saved:")
            for name, path in paths.items():
                print(f"  - {name}: {path}")

        return result
