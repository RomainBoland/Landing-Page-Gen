#!/usr/bin/env python3
"""Demo script to render the v1.2 canonical example with all new features."""

import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.schemas import CanonicalData
from core.renderer import render_landing, render_all_variants

def main():
    # Load the v1.2 example
    example_path = Path(__file__).parent / "canonical_example_v1.2.json"

    with open(example_path, "r", encoding="utf-8") as f:
        data_dict = json.load(f)

    # Parse into CanonicalData
    data = CanonicalData.model_validate(data_dict)

    print(f"Loaded: {data.project.product_name}")
    print(f"Schema version: {data.meta.schema_version}")
    print(f"Tone: {data.project.tone}")
    print(f"Sections enabled: {data.content.sections}")
    print(f"Assets configured: hero_image_prompt={bool(data.assets.hero_image_prompt)}")
    print()

    # Create output directory
    output_dir = Path(__file__).parent.parent / "output" / "v1.2_demo"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Render single page (saas template)
    html = render_landing(data)
    output_path = output_dir / "index.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Rendered: {output_path}")

    # Render all variants
    all_variants = render_all_variants(data)
    for key, html_content in all_variants.items():
        variant_path = output_dir / f"{key}.html"
        with open(variant_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"Rendered: {variant_path}")

    print()
    print(f"Total files generated: {len(all_variants) + 1}")
    print(f"Output directory: {output_dir}")

    # Print sections visibility summary
    print("\n--- Sections Visibility ---")
    sections = data.content.sections
    print(f"  feature_grid: {'VISIBLE' if sections.feature_grid else 'HIDDEN'}")
    print(f"  pricing:      {'VISIBLE' if sections.pricing else 'HIDDEN'}")
    print(f"  faq:          {'VISIBLE' if sections.faq else 'HIDDEN'}")
    print(f"  logos:        {'VISIBLE' if sections.logos else 'HIDDEN'}")
    print(f"  screenshots:  {'VISIBLE' if sections.screenshots else 'HIDDEN'}")
    print(f"  stats:        {'VISIBLE' if sections.stats else 'HIDDEN'}")

if __name__ == "__main__":
    main()
