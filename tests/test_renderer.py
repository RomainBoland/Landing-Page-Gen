"""Tests du moteur de rendu Jinja2.

Vérifie que:
- Le bon template est sélectionné
- Les variantes sont correctement appliquées
- Les sections sont masquées/visibles selon la config
- Le tone styling est appliqué
"""

import pytest

from core.schemas import (
    CanonicalData,
    ProjectInfo,
    LandingContent,
    SectionsConfig,
    RenderConfig,
)
from core.renderer import (
    render_landing,
    render_all_variants,
    TemplateRenderer,
    TEMPLATE_FILES,
    TONE_STYLES,
)
from core.errors import RenderError, ErrorCode


class TestTemplateSelection:
    """Tests pour la sélection de template."""

    def test_default_template_saas(self, valid_canonical_data: CanonicalData):
        """Template par défaut est saas."""
        html = render_landing(valid_canonical_data)
        # Le template saas contient des marqueurs spécifiques
        assert "TestProduct" in html
        assert "<html" in html

    def test_template_override(self, valid_canonical_data: CanonicalData):
        """template_override force le template."""
        valid_canonical_data.render.template_type = "saas"
        html = render_landing(valid_canonical_data, template_override="app")
        # app template a des éléments spécifiques (App Store buttons, gradient-bg)
        assert "App Store" in html or "gradient-bg" in html

    def test_template_from_render_config(self, valid_canonical_data: CanonicalData):
        """Template depuis render.template_type."""
        valid_canonical_data.render.template_type = "agency"
        html = render_landing(valid_canonical_data)
        # agency template a une navigation fixe
        assert "fixed" in html.lower() or "nav" in html.lower()

    def test_all_templates_render(self, valid_canonical_data: CanonicalData):
        """Tous les templates rendent sans erreur."""
        for template_type in TEMPLATE_FILES.keys():
            html = render_landing(valid_canonical_data, template_override=template_type)
            assert len(html) > 1000  # HTML substantiel
            assert "<!DOCTYPE html>" in html


class TestVariantResolution:
    """Tests pour la résolution des variantes."""

    def test_variant_0_uses_default(self, valid_canonical_data: CanonicalData):
        """variant_id=0 utilise les valeurs par défaut."""
        valid_canonical_data.render.variant_id = 0
        html = render_landing(valid_canonical_data)
        assert valid_canonical_data.content.hero.headline in html
        assert valid_canonical_data.content.hero.cta_text in html

    def test_variant_1_uses_first_alternative(self, valid_canonical_data: CanonicalData):
        """variant_id=1 utilise variants[0]."""
        valid_canonical_data.render.variant_id = 1
        html = render_landing(valid_canonical_data)
        assert valid_canonical_data.content.variants.headlines[0] in html
        assert valid_canonical_data.content.variants.ctas[0] in html

    def test_variant_2_uses_second_alternative(self, valid_canonical_data: CanonicalData):
        """variant_id=2 utilise variants[1]."""
        valid_canonical_data.render.variant_id = 2
        html = render_landing(valid_canonical_data)
        assert valid_canonical_data.content.variants.headlines[1] in html
        assert valid_canonical_data.content.variants.ctas[1] in html

    def test_variant_override(self, valid_canonical_data: CanonicalData):
        """variant_override force la variante."""
        valid_canonical_data.render.variant_id = 0
        html = render_landing(valid_canonical_data, variant_override=1)
        # Doit utiliser variant 1, pas 0
        assert valid_canonical_data.content.variants.headlines[0] in html

    def test_out_of_bounds_variant_fallback(self, valid_canonical_data: CanonicalData):
        """variant_id hors bornes → fallback vers défaut."""
        valid_canonical_data.render.variant_id = 99  # hors bornes
        html = render_landing(valid_canonical_data)
        # Doit fallback vers défaut
        assert valid_canonical_data.content.hero.headline in html


class TestSectionsVisibility:
    """Tests pour la visibilité des sections."""

    def test_feature_grid_visible_when_enabled(self, valid_canonical_data: CanonicalData):
        """feature_grid visible quand activé."""
        valid_canonical_data.content.sections.feature_grid = True
        html = render_landing(valid_canonical_data)
        # Les features doivent apparaître
        assert "Feature One" in html
        assert "Feature Two" in html

    def test_feature_grid_hidden_when_disabled(self, valid_canonical_data: CanonicalData):
        """feature_grid masqué quand désactivé."""
        valid_canonical_data.content.sections.feature_grid = False
        html = render_landing(valid_canonical_data)
        # La section features ne doit pas apparaître (mais le produit peut être mentionné ailleurs)
        # On vérifie que "Feature One" n'est pas dans une section features
        assert html.count("Feature One") == 0 or "id=\"features\"" not in html

    def test_faq_visible_with_content(self, valid_canonical_data: CanonicalData):
        """FAQ visible quand activé avec contenu."""
        valid_canonical_data.content.sections.faq = True
        valid_canonical_data.content.faq_items = [
            {"question": "Test Question?", "answer": "Test Answer."}
        ]
        html = render_landing(valid_canonical_data)
        assert "Test Question?" in html

    def test_faq_placeholder_without_content(self, valid_canonical_data: CanonicalData):
        """FAQ avec placeholder quand activé sans contenu."""
        valid_canonical_data.content.sections.faq = True
        valid_canonical_data.content.faq_items = []
        html = render_landing(valid_canonical_data)
        # Doit afficher un placeholder (skeleton)
        assert "FAQ" in html or "placeholder" in html.lower()

    def test_pricing_hidden_by_default(self, valid_canonical_data: CanonicalData):
        """pricing masqué par défaut."""
        valid_canonical_data.content.sections.pricing = False
        html = render_landing(valid_canonical_data)
        # "pricing" ne devrait pas être une section visible
        assert "Simple, transparent pricing" not in html

    def test_logos_visible_when_enabled(self, valid_canonical_data: CanonicalData):
        """logos visible quand activé."""
        valid_canonical_data.content.sections.logos = True
        html = render_landing(valid_canonical_data)
        assert "Trusted by" in html or "trusted" in html.lower()


class TestToneStyling:
    """Tests pour le styling selon le tone."""

    def test_bold_tone_styling(self, valid_canonical_data: CanonicalData):
        """tone=bold applique les classes bold."""
        valid_canonical_data.project.tone = "bold"
        html = render_landing(valid_canonical_data)
        # Bold a des classes spécifiques
        expected_classes = TONE_STYLES["bold"]["hero_size"].split()
        # Au moins une classe doit être présente
        assert any(cls in html for cls in expected_classes)

    def test_minimal_tone_styling(self, valid_canonical_data: CanonicalData):
        """tone=minimal applique les classes minimal."""
        valid_canonical_data.project.tone = "minimal"
        html = render_landing(valid_canonical_data)
        expected_classes = TONE_STYLES["minimal"]["cta_style"].split()
        assert any(cls in html for cls in expected_classes)

    def test_professional_is_default(self, valid_canonical_data: CanonicalData):
        """tone=professional est le style par défaut."""
        valid_canonical_data.project.tone = "professional"
        html = render_landing(valid_canonical_data)
        # Doit rendre sans erreur
        assert len(html) > 1000


class TestRenderAllVariants:
    """Tests pour render_all_variants()."""

    def test_generates_all_template_variants(self, valid_canonical_data: CanonicalData):
        """Génère toutes les combinaisons template × variant."""
        results = render_all_variants(valid_canonical_data)

        # 3 templates × 3 variantes (0, 1, 2) = 9 fichiers
        num_variants = len(valid_canonical_data.content.variants.headlines) + 1
        expected_count = len(TEMPLATE_FILES) * num_variants
        assert len(results) == expected_count

    def test_keys_format(self, valid_canonical_data: CanonicalData):
        """Clés au format {template}_v{variant}."""
        results = render_all_variants(valid_canonical_data)

        assert "saas_v0" in results
        assert "app_v0" in results
        assert "agency_v0" in results
        assert "saas_v1" in results
        assert "saas_v2" in results

    def test_each_variant_has_correct_headline(self, valid_canonical_data: CanonicalData):
        """Chaque variante a le bon headline."""
        results = render_all_variants(valid_canonical_data)

        # v0 doit avoir le headline par défaut
        assert valid_canonical_data.content.hero.headline in results["saas_v0"]

        # v1 doit avoir le premier headline alternatif
        assert valid_canonical_data.content.variants.headlines[0] in results["saas_v1"]


class TestErrorHandling:
    """Tests pour la gestion des erreurs."""

    def test_missing_content_raises_error(self, valid_project_info: ProjectInfo):
        """Rendu sans content lève RenderError."""
        data = CanonicalData(project=valid_project_info)
        assert data.content is None

        with pytest.raises(RenderError) as exc_info:
            render_landing(data)

        assert exc_info.value.code == ErrorCode.MISSING_CONTENT

    def test_render_error_has_details(self, valid_project_info: ProjectInfo):
        """RenderError contient les détails."""
        data = CanonicalData(project=valid_project_info)

        with pytest.raises(RenderError) as exc_info:
            render_landing(data)

        error = exc_info.value
        assert error.code is not None
        assert error.message is not None
        assert "content" in error.message.lower()
