"""Tests de validation des schémas Pydantic.

Vérifie que:
- Les JSON valides sont acceptés
- Les JSON invalides lèvent ValidationError
- Les contraintes (min/max, patterns) sont respectées
"""

import pytest
from pydantic import ValidationError

from core.schemas import (
    UserInput,
    ProjectInfo,
    BrandIdentity,
    ColorPalette,
    Typography,
    Feature,
    HeroSection,
    LandingContent,
    CanonicalData,
    ContentVariants,
    SectionsConfig,
    GenerationMeta,
    SCHEMA_VERSION,
    ALLOWED_FONTS,
    ALLOWED_ICONS,
    TONE_PRESETS,
)


class TestUserInput:
    """Tests pour UserInput."""

    def test_valid_minimal(self):
        """UserInput valide avec valeurs par défaut."""
        user_input = UserInput(
            product_name="MyProduct",
            target_audience="Developers",
            value_proposition="Save time",
        )
        assert user_input.product_name == "MyProduct"
        assert user_input.tone == "professional"  # défaut
        assert user_input.template_type == "saas"  # défaut

    def test_valid_all_fields(self):
        """UserInput valide avec tous les champs."""
        user_input = UserInput(
            product_name="MyProduct",
            target_audience="Developers",
            value_proposition="Save time",
            tone="bold",
            template_type="app",
            additional_context="Some context",
        )
        assert user_input.tone == "bold"
        assert user_input.template_type == "app"

    def test_invalid_empty_product_name(self):
        """product_name vide doit échouer."""
        with pytest.raises(ValidationError) as exc_info:
            UserInput(
                product_name="",
                target_audience="Developers",
                value_proposition="Save time",
            )
        assert "product_name" in str(exc_info.value)

    def test_invalid_whitespace_only(self):
        """product_name avec espaces uniquement doit échouer."""
        with pytest.raises(ValidationError):
            UserInput(
                product_name="   ",
                target_audience="Developers",
                value_proposition="Save time",
            )

    def test_invalid_tone(self):
        """tone invalide doit échouer."""
        with pytest.raises(ValidationError) as exc_info:
            UserInput(
                product_name="MyProduct",
                target_audience="Developers",
                value_proposition="Save time",
                tone="invalid_tone",  # type: ignore
            )
        assert "tone" in str(exc_info.value).lower()

    def test_invalid_template_type(self):
        """template_type invalide doit échouer."""
        with pytest.raises(ValidationError):
            UserInput(
                product_name="MyProduct",
                target_audience="Developers",
                value_proposition="Save time",
                template_type="invalid",  # type: ignore
            )


class TestProjectInfo:
    """Tests pour ProjectInfo."""

    def test_valid(self, valid_project_info: ProjectInfo):
        """ProjectInfo valide."""
        assert valid_project_info.product_name == "TestProduct"
        assert valid_project_info.tone in TONE_PRESETS

    def test_keywords_normalized_lowercase(self):
        """keywords doivent être normalisés en lowercase."""
        project = ProjectInfo(
            product_name="Test",
            tagline="Test tagline",
            description="Test description that is long enough.",
            target_audience="Testers",
            value_proposition="Testing",
            tone="professional",
            keywords=["TEST", "Keyword", "UPPER"],
        )
        assert project.keywords == ["test", "keyword", "upper"]

    def test_keywords_minimum_required(self):
        """Minimum 3 keywords requis."""
        with pytest.raises(ValidationError) as exc_info:
            ProjectInfo(
                product_name="Test",
                tagline="Test tagline",
                description="Test description that is long enough.",
                target_audience="Testers",
                value_proposition="Testing",
                tone="professional",
                keywords=["one", "two"],  # seulement 2
            )
        assert "keyword" in str(exc_info.value).lower()

    def test_tagline_max_length(self):
        """tagline ne doit pas dépasser 80 caractères."""
        with pytest.raises(ValidationError):
            ProjectInfo(
                product_name="Test",
                tagline="A" * 81,  # 81 caractères
                description="Test description that is long enough.",
                target_audience="Testers",
                value_proposition="Testing",
                tone="professional",
                keywords=["one", "two", "three"],
            )


class TestColorPalette:
    """Tests pour ColorPalette."""

    def test_valid_hex_colors(self):
        """Couleurs hex valides."""
        palette = ColorPalette(
            primary="#FF6B35",
            secondary="#818CF8",
            accent="#10B981",
            background="#FFFFFF",
            text="#000000",
        )
        assert palette.primary == "#FF6B35"

    def test_invalid_hex_no_hash(self):
        """Couleur sans # doit échouer."""
        with pytest.raises(ValidationError):
            ColorPalette(
                primary="FF6B35",  # manque #
                secondary="#818CF8",
                accent="#10B981",
                background="#FFFFFF",
                text="#000000",
            )

    def test_invalid_hex_short(self):
        """Couleur hex courte (3 chars) doit échouer."""
        with pytest.raises(ValidationError):
            ColorPalette(
                primary="#F00",  # format court non supporté
                secondary="#818CF8",
                accent="#10B981",
                background="#FFFFFF",
                text="#000000",
            )

    def test_invalid_hex_characters(self):
        """Caractères invalides dans hex doivent échouer."""
        with pytest.raises(ValidationError):
            ColorPalette(
                primary="#GGGGGG",  # G invalide
                secondary="#818CF8",
                accent="#10B981",
                background="#FFFFFF",
                text="#000000",
            )


class TestTypography:
    """Tests pour Typography."""

    def test_valid_fonts(self):
        """Fonts valides de ALLOWED_FONTS."""
        typo = Typography(heading="Inter", body="Roboto")
        assert typo.heading == "Inter"
        assert typo.body == "Roboto"

    def test_invalid_font_raises_error(self):
        """Font non autorisée doit lever une erreur (pas de fallback)."""
        with pytest.raises(ValidationError) as exc_info:
            Typography(heading="Comic Sans", body="Inter")
        assert "ALLOWED_FONTS" in str(exc_info.value)

    def test_all_allowed_fonts_valid(self):
        """Toutes les fonts de ALLOWED_FONTS sont acceptées."""
        for font in list(ALLOWED_FONTS)[:5]:  # Test quelques fonts
            typo = Typography(heading=font, body=font)
            assert typo.heading == font


class TestFeature:
    """Tests pour Feature."""

    def test_valid_icon(self):
        """Icône valide de ALLOWED_ICONS."""
        feature = Feature(
            title="Test Feature",
            description="This is a test feature description.",
            icon="rocket",
        )
        assert feature.icon == "rocket"

    def test_icon_normalized_lowercase(self):
        """Icône normalisée en lowercase."""
        feature = Feature(
            title="Test Feature",
            description="This is a test feature description.",
            icon="ROCKET",
        )
        assert feature.icon == "rocket"

    def test_invalid_icon_raises_error(self):
        """Icône invalide doit lever une erreur."""
        with pytest.raises(ValidationError) as exc_info:
            Feature(
                title="Test Feature",
                description="This is a test feature description.",
                icon="invalid_icon",
            )
        assert "ALLOWED_ICONS" in str(exc_info.value)


class TestContentVariants:
    """Tests pour ContentVariants."""

    def test_empty_variants(self):
        """Variantes vides par défaut."""
        variants = ContentVariants()
        assert variants.headlines == []
        assert variants.ctas == []
        assert variants.max_variant_id() == 0

    def test_max_variant_id_calculation(self):
        """max_variant_id() retourne le bon nombre."""
        variants = ContentVariants(
            headlines=["H1", "H2", "H3"],
            ctas=["C1", "C2"],
        )
        assert variants.max_variant_id() == 3  # basé sur headlines

    def test_empty_strings_filtered(self):
        """Strings vides sont filtrées."""
        variants = ContentVariants(
            headlines=["H1", "", "  ", "H2"],
            ctas=["C1"],
        )
        assert variants.headlines == ["H1", "H2"]


class TestSectionsConfig:
    """Tests pour SectionsConfig."""

    def test_defaults(self):
        """Valeurs par défaut correctes."""
        sections = SectionsConfig()
        assert sections.feature_grid is True
        assert sections.stats is True
        assert sections.pricing is False
        assert sections.faq is False

    def test_enabled_sections(self):
        """enabled_sections() retourne les sections actives."""
        sections = SectionsConfig(
            feature_grid=True,
            faq=True,
            pricing=False,
        )
        enabled = sections.enabled_sections()
        assert "feature_grid" in enabled
        assert "faq" in enabled
        assert "pricing" not in enabled


class TestGenerationMeta:
    """Tests pour GenerationMeta."""

    def test_default_schema_version(self):
        """schema_version par défaut est SCHEMA_VERSION."""
        meta = GenerationMeta()
        assert meta.schema_version == SCHEMA_VERSION

    def test_valid_compatible_version(self):
        """Versions compatibles (même majeure.mineure) acceptées."""
        meta = GenerationMeta(schema_version=SCHEMA_VERSION)
        assert meta.schema_version == SCHEMA_VERSION

    def test_invalid_major_version_mismatch(self):
        """Version majeure différente doit échouer."""
        with pytest.raises(ValidationError) as exc_info:
            GenerationMeta(schema_version="2.2.0")
        assert "mismatch" in str(exc_info.value).lower()

    def test_invalid_minor_version_mismatch(self):
        """Version mineure différente doit échouer."""
        with pytest.raises(ValidationError):
            GenerationMeta(schema_version="1.0.0")

    def test_invalid_version_format(self):
        """Format de version invalide doit échouer."""
        with pytest.raises(ValidationError):
            GenerationMeta(schema_version="invalid")


class TestCanonicalData:
    """Tests pour CanonicalData."""

    def test_valid_complete(self, valid_canonical_data: CanonicalData):
        """CanonicalData complet et valide."""
        assert valid_canonical_data.project.product_name == "TestProduct"
        assert valid_canonical_data.brand is not None
        assert valid_canonical_data.content is not None

    def test_valid_minimal(self, valid_project_info: ProjectInfo):
        """CanonicalData minimal (sans brand/content)."""
        data = CanonicalData(project=valid_project_info)
        assert data.brand is None
        assert data.content is None
        assert data.render.template_type == "saas"

    def test_from_json_valid(self, minimal_canonical_json: str):
        """Chargement depuis JSON valide."""
        data = CanonicalData.from_json(minimal_canonical_json)
        assert data.project.product_name == "MinimalTest"

    def test_from_json_invalid(self):
        """JSON invalide doit lever ValidationError."""
        invalid_json = '{"project": {}}'  # project incomplet
        with pytest.raises(ValidationError):
            CanonicalData.from_json(invalid_json)

    def test_add_step(self, valid_canonical_data: CanonicalData):
        """add_step() ajoute au journal."""
        initial_steps = len(valid_canonical_data.meta.pipeline_steps)
        valid_canonical_data.add_step("test_step")
        assert len(valid_canonical_data.meta.pipeline_steps) == initial_steps + 1
        assert "test_step" in valid_canonical_data.meta.pipeline_steps

    def test_get_effective_variant_id_in_bounds(self, valid_canonical_data: CanonicalData):
        """get_effective_variant_id() retourne variant_id si valide."""
        valid_canonical_data.render.variant_id = 1
        assert valid_canonical_data.get_effective_variant_id() == 1

    def test_get_effective_variant_id_out_of_bounds(self, valid_canonical_data: CanonicalData):
        """get_effective_variant_id() retourne 0 si hors bornes."""
        valid_canonical_data.render.variant_id = 99
        assert valid_canonical_data.get_effective_variant_id() == 0

    def test_to_json_roundtrip(self, valid_canonical_data: CanonicalData):
        """Sérialisation/désérialisation roundtrip."""
        json_str = valid_canonical_data.to_json()
        loaded = CanonicalData.from_json(json_str)
        assert loaded.project.product_name == valid_canonical_data.project.product_name
        assert loaded.brand.colors.primary == valid_canonical_data.brand.colors.primary
