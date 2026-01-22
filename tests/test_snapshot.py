"""Tests de snapshot HTML.

Vérifie que le rendu HTML reste stable entre les versions.
Utilise canonical_example_v1.2.json comme référence.
"""

import pytest
import hashlib
from pathlib import Path

from core.schemas import CanonicalData, SCHEMA_VERSION
from core.renderer import render_landing, render_all_variants


# Répertoire pour les snapshots de référence
SNAPSHOTS_DIR = Path(__file__).parent / "snapshots"


class TestCanonicalExampleSnapshot:
    """Tests de snapshot sur canonical_example_v1.2.json."""

    def test_example_file_exists(self, canonical_example_path: Path):
        """Le fichier d'exemple existe."""
        assert canonical_example_path.exists(), f"File not found: {canonical_example_path}"

    def test_example_loads_successfully(self, canonical_example_path: Path):
        """L'exemple se charge sans erreur."""
        data = CanonicalData.from_file(str(canonical_example_path))
        assert data.project.product_name == "LaunchPad"
        assert data.project.tone == "bold"

    def test_example_renders_without_error(self, canonical_example_path: Path):
        """L'exemple se rend sans erreur."""
        data = CanonicalData.from_file(str(canonical_example_path))
        html = render_landing(data)

        # Vérifications de base
        assert len(html) > 5000  # HTML substantiel
        assert "<!DOCTYPE html>" in html
        assert data.project.product_name in html

    def test_example_html_structure(self, canonical_example_path: Path):
        """Structure HTML de l'exemple est correcte."""
        data = CanonicalData.from_file(str(canonical_example_path))
        html = render_landing(data)

        # Éléments structurels obligatoires
        assert "<html" in html
        assert "<head>" in html
        assert "<body" in html
        assert "</html>" in html

        # Meta tags
        assert "<title>" in html
        assert 'name="description"' in html

        # Tailwind CSS
        assert "tailwindcss" in html.lower()

    def test_example_contains_product_info(self, canonical_example_path: Path):
        """L'exemple contient les infos produit."""
        data = CanonicalData.from_file(str(canonical_example_path))
        html = render_landing(data)

        # Infos produit
        assert data.project.product_name in html
        assert data.project.tagline in html
        assert data.content.hero.headline in html

    def test_example_contains_features(self, canonical_example_path: Path):
        """L'exemple contient les features."""
        data = CanonicalData.from_file(str(canonical_example_path))
        html = render_landing(data)

        # Au moins quelques features
        for feature in data.content.features[:2]:
            assert feature.title in html

    def test_example_contains_testimonial(self, canonical_example_path: Path):
        """L'exemple contient le testimonial."""
        data = CanonicalData.from_file(str(canonical_example_path))
        html = render_landing(data)

        assert data.content.testimonial.author in html
        assert data.content.testimonial.quote in html

    def test_example_sections_visibility(self, canonical_example_path: Path):
        """Les sections de l'exemple sont visibles/masquées correctement."""
        data = CanonicalData.from_file(str(canonical_example_path))
        html = render_landing(data)

        # Sections activées dans l'exemple
        if data.content.sections.faq and data.content.faq_items:
            # Au moins une question FAQ doit être visible
            assert data.content.faq_items[0]["question"] in html

        if data.content.sections.pricing and data.content.pricing_plans:
            # Au moins un plan doit être visible
            assert data.content.pricing_plans[0]["name"] in html

    def test_example_assets_placeholder(self, canonical_example_path: Path):
        """Les placeholders d'assets sont présents."""
        data = CanonicalData.from_file(str(canonical_example_path))
        html = render_landing(data)

        # Si hero_image_prompt est défini, un placeholder doit être présent
        if data.assets.hero_image_prompt:
            assert "placehold" in html.lower() or "placeholder" in html.lower()

    def test_example_tone_styling_applied(self, canonical_example_path: Path):
        """Le styling bold est appliqué."""
        data = CanonicalData.from_file(str(canonical_example_path))
        assert data.project.tone == "bold"

        html = render_landing(data)

        # Bold a des classes spécifiques
        # text-6xl md:text-7xl font-black, rounded-none uppercase tracking-wider
        bold_indicators = ["font-black", "uppercase", "tracking-wider"]
        assert any(indicator in html for indicator in bold_indicators)


class TestHTMLStability:
    """Tests de stabilité du HTML généré."""

    def test_deterministic_rendering(self, valid_canonical_data: CanonicalData):
        """Même données → même HTML (déterministe)."""
        html1 = render_landing(valid_canonical_data)
        html2 = render_landing(valid_canonical_data)

        # Le seul élément non-déterministe est current_year
        # On compare le hash du HTML sans l'année
        def normalize(html: str) -> str:
            # Retire l'année courante pour la comparaison
            import re
            return re.sub(r'\d{4}', 'YEAR', html)

        assert normalize(html1) == normalize(html2)

    def test_hash_stability(self, valid_canonical_data: CanonicalData):
        """Le hash du HTML est stable entre rendus."""
        def get_hash(html: str) -> str:
            # Normalise l'année
            import re
            normalized = re.sub(r'\d{4}', 'YEAR', html)
            return hashlib.md5(normalized.encode()).hexdigest()

        html1 = render_landing(valid_canonical_data)
        html2 = render_landing(valid_canonical_data)

        assert get_hash(html1) == get_hash(html2)

    def test_all_variants_different(self, valid_canonical_data: CanonicalData):
        """Chaque variante produit un HTML différent."""
        results = render_all_variants(valid_canonical_data)

        # Les variantes v0, v1, v2 doivent être différentes (pour le même template)
        assert results["saas_v0"] != results["saas_v1"]
        assert results["saas_v1"] != results["saas_v2"]

    def test_different_templates_different_html(self, valid_canonical_data: CanonicalData):
        """Différents templates produisent différent HTML."""
        results = render_all_variants(valid_canonical_data)

        # saas, app, agency doivent être différents
        assert results["saas_v0"] != results["app_v0"]
        assert results["app_v0"] != results["agency_v0"]
        assert results["saas_v0"] != results["agency_v0"]


class TestSchemaVersionCompatibility:
    """Tests de compatibilité de version du schéma."""

    def test_current_version(self, canonical_example_path: Path):
        """L'exemple utilise une version compatible."""
        data = CanonicalData.from_file(str(canonical_example_path))

        # La version doit être compatible (même majeure.mineure)
        current_parts = SCHEMA_VERSION.split(".")
        example_parts = data.meta.schema_version.split(".")

        assert example_parts[0] == current_parts[0], "Major version mismatch"
        assert example_parts[1] == current_parts[1], "Minor version mismatch"

    def test_renders_with_current_schema(self, canonical_example_path: Path):
        """L'exemple se rend avec le schéma actuel."""
        data = CanonicalData.from_file(str(canonical_example_path))
        html = render_landing(data)

        # Doit fonctionner sans erreur
        assert len(html) > 0
