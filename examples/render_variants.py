"""Démonstration: Un même JSON canonique → Plusieurs HTML différents.

Ce script montre comment:
1. Charger un canonical.json existant
2. Générer des HTML avec différents templates (saas, app, agency)
3. Générer des HTML avec différentes variantes de contenu (headlines, CTAs)

Usage:
    python examples/render_variants.py
"""

from pathlib import Path
import sys

# Ajout du chemin parent pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.schemas import CanonicalData
from core.renderer import render_landing, render_all_variants, TEMPLATE_FILES


def main():
    # 1. Charger le JSON canonique
    example_path = Path(__file__).parent / "canonical_example.json"
    print(f"Loading: {example_path}")

    with open(example_path, "r", encoding="utf-8") as f:
        data = CanonicalData.from_json(f.read())

    print(f"\nProduct: {data.project.product_name}")
    print(f"Default template: {data.render.template_type}")
    print(f"Default variant: {data.render.variant_id}")

    # 2. Préparer le dossier output
    output_dir = Path(__file__).parent.parent / "output" / "variants_demo"
    output_dir.mkdir(parents=True, exist_ok=True)

    # 3. Générer quelques combinaisons spécifiques pour démonstration
    print("\n" + "="*60)
    print("GENERATING SPECIFIC COMBINATIONS")
    print("="*60)

    combinations = [
        # (template, variant, description)
        ("saas", 0, "SaaS template, default content"),
        ("saas", 1, "SaaS template, variant headline #1"),
        ("app", 0, "App template, default content"),
        ("agency", 0, "Agency template, default content"),
    ]

    for template, variant, desc in combinations:
        html = render_landing(data, template_override=template, variant_override=variant)
        filename = f"{template}_v{variant}.html"
        filepath = output_dir / filename
        filepath.write_text(html, encoding="utf-8")
        print(f"  ✓ {filename:20} → {desc}")

    # 4. Générer TOUTES les combinaisons
    print("\n" + "="*60)
    print("GENERATING ALL VARIANTS")
    print("="*60)

    all_variants = render_all_variants(data)
    all_dir = output_dir / "all"
    all_dir.mkdir(exist_ok=True)

    for key, html in all_variants.items():
        filepath = all_dir / f"{key}.html"
        filepath.write_text(html, encoding="utf-8")
        print(f"  ✓ {key}.html")

    # 5. Résumé
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"\nInput:  1 canonical.json")
    print(f"Output: {len(all_variants)} HTML files")
    print(f"\nTemplates disponibles: {', '.join(TEMPLATE_FILES.keys())}")
    print(f"Variantes de headline: {len(data.content.variants.headlines)}")
    print(f"Variantes de CTA: {len(data.content.variants.ctas)}")
    print(f"\nFichiers générés dans: {output_dir}")

    # 6. Montrer les différences de headline
    print("\n" + "="*60)
    print("CONTENT VARIATIONS")
    print("="*60)
    print(f"\nHeadline (default): {data.content.hero.headline}")
    for i, h in enumerate(data.content.variants.headlines, 1):
        print(f"Headline (v{i}):      {h}")

    print(f"\nCTA (default): {data.content.hero.cta_text}")
    for i, c in enumerate(data.content.variants.ctas, 1):
        print(f"CTA (v{i}):      {c}")


if __name__ == "__main__":
    main()
