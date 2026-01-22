# Landing Generator v1.2.1

AI-powered landing page generator with Pydantic schemas, LLM agents, and Jinja2 templates.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run with example
python main.py --example 1

# Render from JSON
python main.py --input examples/canonical_example_v1.2.json --output output/

# Render all variants
python main.py --input examples/canonical_example_v1.2.json --output output/ --all-variants
```

## Project Structure

```
landing-generator/
├── core/                      # Core modules
│   ├── schemas.py            # Pydantic schemas (source of truth)
│   ├── renderer.py           # Jinja2 template engine
│   ├── errors.py             # Custom exceptions
│   ├── logging_config.py     # Logging configuration
│   └── llm.py                # LLM client abstraction
├── agents/                    # LLM agents
│   ├── base.py               # Base agent class
│   ├── onboarding.py         # UserInput → ProjectInfo
│   ├── brand.py              # ProjectInfo → BrandIdentity
│   └── landing.py            # CanonicalData → LandingContent + HTML
├── templates/                 # Jinja2 HTML templates
│   ├── saas.html.j2          # SaaS template (clean, professional)
│   ├── app.html.j2           # App template (bold, mobile-first)
│   └── agency.html.j2        # Agency template (elegant, minimal)
├── tests/                     # Pytest tests
│   ├── test_schemas.py       # Schema validation tests
│   ├── test_renderer.py      # Renderer tests
│   └── test_snapshot.py      # HTML snapshot tests
├── examples/                  # Example files
│   ├── canonical_example_v1.2.json
│   └── demo.py
├── output/                    # Generated output (gitignored)
├── main.py                    # CLI entry point
├── orchestrator.py            # Pipeline orchestration
└── README.md
```

## Architecture

### Data Flow

```
UserInput
    ↓ [OnboardingAgent]
ProjectInfo
    ↓ [BrandAgent]
BrandIdentity
    ↓ [LandingAgent]
LandingContent + HTML
    ↓ [Save]
output/
  ├── canonical.json
  └── index.html
```

### JSON Schema (v1.2.1)

The canonical JSON is the single source of truth:

```json
{
  "meta": {
    "schema_version": "1.2.1",
    "generated_at": "2024-01-15T10:30:00",
    "pipeline_steps": ["onboarding", "brand", "landing"]
  },
  "project": {
    "product_name": "MyProduct",
    "tagline": "Short tagline",
    "description": "...",
    "tone": "professional|friendly|bold|minimal",
    "keywords": ["keyword1", "keyword2", "keyword3"]
  },
  "brand": {
    "colors": { "primary": "#6366F1", ... },
    "fonts": { "heading": "Inter", "body": "Inter" },
    "tone_rules": ["Rule 1", "Rule 2"]
  },
  "content": {
    "hero": { "headline": "...", "subheadline": "...", "cta_text": "..." },
    "features": [...],
    "testimonial": {...},
    "variants": { "headlines": [...], "ctas": [...] },
    "sections": { "pricing": false, "faq": true, ... }
  },
  "assets": {
    "hero_image_prompt": "...",
    "og_image_prompt": "..."
  },
  "render": {
    "template_type": "saas|app|agency",
    "variant_id": 0
  }
}
```

## CLI Usage

```bash
# Full pipeline with LLM
python main.py --example 1              # Use built-in example 1-5
python main.py --example all            # Run all examples

# Render from existing JSON (no LLM required)
python main.py --input path/to/canonical.json --output output/

# Render all template × variant combinations
python main.py --input canonical.json --output output/ --all-variants

# Verbose logging
python main.py --input canonical.json --output output/ --verbose
```

## Configuration

### Templates

| Template | Style | Best for |
|----------|-------|----------|
| `saas` | Clean, professional | B2B SaaS products |
| `app` | Bold, mobile-first | Consumer apps |
| `agency` | Elegant, minimal | Creative agencies |

### Tones

| Tone | Style | CTA Examples |
|------|-------|--------------|
| `professional` | Formal, trust-building | "Get Started", "Request Demo" |
| `friendly` | Warm, conversational | "Try it free", "See how it works" |
| `bold` | Direct, punchy | "Start Now", "Claim Your Spot" |
| `minimal` | Understated, elegant | "Explore", "Learn more" |

### Sections

```python
sections = {
    "feature_grid": True,   # Default: True
    "stats": True,          # Default: True
    "pricing": False,       # Default: False
    "faq": False,           # Default: False
    "logos": False,         # Default: False
    "screenshots": False,   # Default: False
}
```

## Rendering Rules

### Variant Resolution

```
variant_id=0 → hero.headline, hero.cta_text (default)
variant_id=1 → variants.headlines[0], variants.ctas[0]
variant_id=2 → variants.headlines[1], variants.ctas[1]
variant_id=N (out of bounds) → fallback to default
```

### Section Behavior

```
section.enabled=True  + data exists  → Render section
section.enabled=True  + no data      → Render placeholder
section.enabled=False                → Hidden (not rendered)
```

## Development

### Install Dependencies

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For testing
```

### Run Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=core --cov=agents

# Specific test file
pytest tests/test_schemas.py -v

# Only snapshot tests
pytest tests/test_snapshot.py -v
```

### Code Structure

#### Where to modify...

| To change... | Edit file |
|--------------|-----------|
| Schema fields | `core/schemas.py` |
| Validation rules | `core/schemas.py` |
| Template HTML | `templates/*.html.j2` |
| Render logic | `core/renderer.py` |
| Agent prompts | `agents/*.py` |
| Error handling | `core/errors.py` |
| CLI options | `main.py` |

### Adding a New Section

1. Add field to `SectionsConfig` in `core/schemas.py`
2. Add data model if needed (e.g., `FAQItem`)
3. Add conditional block in templates: `{% if sections.my_section %}`
4. Update `_get_default_sections()` in `agents/landing.py`
5. Add tests in `tests/test_renderer.py`

### Adding a New Template

1. Create `templates/my_template.html.j2`
2. Add to `TEMPLATE_FILES` in `core/renderer.py`
3. Add to `TemplateType` Literal in `core/schemas.py`
4. Add tests for the new template

## Error Handling

All errors inherit from `PipelineError`:

```python
from core.errors import PipelineError, ErrorCode

try:
    html = render_landing(data)
except PipelineError as e:
    print(f"Error {e.code.value}: {e.message}")
    print(f"Details: {e.details}")
```

Error codes:
- `E1xx`: Validation errors
- `E2xx`: Agent errors
- `E3xx`: Render errors
- `E4xx`: IO errors

## Requirements

- Python 3.11+
- pydantic >= 2.0
- jinja2 >= 3.0
- openai >= 1.0 (for LLM agents)

## License

MIT
