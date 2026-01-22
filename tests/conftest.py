"""Pytest fixtures for landing-generator tests."""

import pytest
from pathlib import Path

from core.schemas import (
    CanonicalData,
    ProjectInfo,
    BrandIdentity,
    ColorPalette,
    Typography,
    LandingContent,
    HeroSection,
    Feature,
    Testimonial,
    ContentVariants,
    SectionsConfig,
    AssetSlots,
    RenderConfig,
    GenerationMeta,
    SCHEMA_VERSION,
)


@pytest.fixture
def valid_project_info() -> ProjectInfo:
    """Fixture: ProjectInfo valide minimal."""
    return ProjectInfo(
        product_name="TestProduct",
        tagline="Test tagline here",
        description="This is a test product description that is long enough.",
        target_audience="Developers and testers",
        value_proposition="Make testing easier",
        tone="professional",
        keywords=["test", "fixture", "pytest"],
    )


@pytest.fixture
def valid_brand_identity() -> BrandIdentity:
    """Fixture: BrandIdentity valide."""
    return BrandIdentity(
        colors=ColorPalette(
            primary="#6366F1",
            secondary="#818CF8",
            accent="#F59E0B",
            background="#FAFAFA",
            text="#1F2937",
        ),
        fonts=Typography(heading="Inter", body="Inter"),
        tone_rules=["Be clear", "Be concise", "Focus on benefits"],
    )


@pytest.fixture
def valid_landing_content() -> LandingContent:
    """Fixture: LandingContent valide avec variantes."""
    return LandingContent(
        hero=HeroSection(
            headline="Welcome to TestProduct",
            subheadline="This is the subheadline that explains what we do in detail.",
            cta_text="Get Started",
        ),
        features=[
            Feature(title="Feature One", description="This is the first feature description.", icon="rocket"),
            Feature(title="Feature Two", description="This is the second feature description.", icon="shield"),
            Feature(title="Feature Three", description="This is the third feature description.", icon="zap"),
        ],
        testimonial=Testimonial(
            quote="This product changed everything for our team!",
            author="Jane Doe",
            role="CTO, TechCorp",
        ),
        footer_cta="Ready to get started?",
        variants=ContentVariants(
            headlines=["Alternative Headline One", "Alternative Headline Two"],
            ctas=["Try It Free", "Start Now"],
        ),
        sections=SectionsConfig(
            feature_grid=True,
            faq=True,
            pricing=False,
            logos=True,
            screenshots=False,
            stats=True,
        ),
    )


@pytest.fixture
def valid_canonical_data(
    valid_project_info: ProjectInfo,
    valid_brand_identity: BrandIdentity,
    valid_landing_content: LandingContent,
) -> CanonicalData:
    """Fixture: CanonicalData complet et valide."""
    return CanonicalData(
        meta=GenerationMeta(
            schema_version=SCHEMA_VERSION,
            pipeline_steps=["onboarding", "brand", "landing"],
        ),
        project=valid_project_info,
        brand=valid_brand_identity,
        content=valid_landing_content,
        assets=AssetSlots(
            hero_image_prompt="Test hero image prompt",
            hero_image_alt="Test hero alt text",
        ),
        render=RenderConfig(template_type="saas", variant_id=0),
    )


@pytest.fixture
def canonical_example_path() -> Path:
    """Fixture: Chemin vers canonical_example_v1.2.json."""
    return Path(__file__).parent.parent / "examples" / "canonical_example_v1.2.json"


@pytest.fixture
def minimal_canonical_json() -> str:
    """Fixture: JSON canonique minimal valide."""
    return f'''{{
        "meta": {{"schema_version": "{SCHEMA_VERSION}"}},
        "project": {{
            "product_name": "MinimalTest",
            "tagline": "A minimal test",
            "description": "This is a minimal test product for validation.",
            "target_audience": "Testers",
            "value_proposition": "Test validation",
            "tone": "professional",
            "keywords": ["test", "minimal", "validation"]
        }}
    }}'''
