#!/usr/bin/env python3
"""Landing Page Generator - CLI entry point.

Usage:
    # Run with built-in example
    python main.py --example 1
    python main.py --example all

    # Render from existing JSON (no LLM required)
    python main.py --input canonical.json --output output/

    # Render all template × variant combinations
    python main.py --input canonical.json --output output/ --all-variants

    # Verbose logging
    python main.py --input canonical.json --output output/ --verbose
"""

import argparse
import sys
import os
from pathlib import Path

# Load environment variables from .env if present
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        if line.strip() and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())

from core.schemas import CanonicalData, SCHEMA_VERSION
from core.renderer import render_landing, render_all_variants
from core.errors import PipelineError
from core.logging_config import configure_logging, get_logger
import logging

logger = get_logger(__name__)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Landing Page Generator v1.2.1",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --example 1                    # Run built-in example 1
  python main.py --example all                  # Run all built-in examples
  python main.py --input data.json -o output/   # Render from JSON
  python main.py --input data.json --all-variants  # Render all combinations

Output structure:
  output/
  ├── canonical.json   # Source of truth
  ├── index.html       # Default render (saas_v0)
  └── variants/        # (with --all-variants)
      ├── saas_v0.html
      ├── saas_v1.html
      ├── app_v0.html
      └── ...
        """,
    )

    # Mode: example OR input file
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        "--example", "-e",
        metavar="N",
        help="Run built-in example (1-5 or 'all')",
    )
    mode_group.add_argument(
        "--input", "-i",
        metavar="FILE",
        help="Path to canonical JSON file (no LLM required)",
    )

    # Output
    parser.add_argument(
        "--output", "-o",
        metavar="DIR",
        default="output",
        help="Output directory (default: ./output)",
    )

    # Render options
    parser.add_argument(
        "--all-variants",
        action="store_true",
        help="Render all template × variant combinations",
    )
    parser.add_argument(
        "--template",
        choices=["saas", "app", "agency"],
        help="Override template type",
    )
    parser.add_argument(
        "--variant",
        type=int,
        metavar="N",
        help="Override variant ID (0=default)",
    )

    # Logging
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging",
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress non-error output",
    )

    return parser.parse_args()


def run_example(example_arg: str, output_dir: Path) -> int:
    """Run built-in example(s) with full LLM pipeline.

    Returns:
        Exit code (0=success, 1=error)
    """
    try:
        from core.llm import OpenAIClient
        from orchestrator import LandingPipeline
        from examples.demo import EXAMPLES
    except ImportError as e:
        logger.error(f"Failed to import required modules: {e}")
        return 1

    # Initialize pipeline
    llm = OpenAIClient()
    pipeline = LandingPipeline(llm)

    if example_arg.lower() == "all":
        examples_to_run = EXAMPLES
    else:
        try:
            idx = int(example_arg) - 1
            if 0 <= idx < len(EXAMPLES):
                examples_to_run = [EXAMPLES[idx]]
            else:
                logger.error(f"Invalid example number. Use 1-{len(EXAMPLES)} or 'all'")
                return 1
        except ValueError:
            logger.error(f"Invalid example: {example_arg}")
            return 1

    # Run examples
    success_count = 0
    for name, user_input in examples_to_run:
        print(f"\n{'='*60}")
        print(f"GENERATING: {name}")
        print(f"{'='*60}")
        print(f"Product: {user_input.product_name}")
        print(f"Tone: {user_input.tone}")
        print(f"Template: {user_input.template_type}")

        product_slug = user_input.product_name.lower().replace(" ", "_")
        example_output_dir = output_dir / product_slug

        result = pipeline.run(user_input, output_dir=str(example_output_dir))

        if result.success:
            logger.info(f"Generated: {example_output_dir}")
            success_count += 1
        else:
            logger.error(f"Failed: {result.errors}")

    print(f"\n{'='*60}")
    print(f"Completed: {success_count}/{len(examples_to_run)} successful")
    print(f"{'='*60}")

    return 0 if success_count == len(examples_to_run) else 1


def run_render(
    input_path: Path,
    output_dir: Path,
    all_variants: bool,
    template_override: str | None,
    variant_override: int | None,
) -> int:
    """Render from existing canonical JSON (no LLM required).

    Returns:
        Exit code (0=success, 1=error)
    """
    # Load canonical data
    logger.info(f"Loading: {input_path}")

    try:
        data = CanonicalData.from_file(str(input_path))
    except FileNotFoundError:
        logger.error(f"File not found: {input_path}")
        return 1
    except Exception as e:
        logger.error(f"Failed to load JSON: {e}")
        return 1

    logger.info(f"Loaded: {data.project.product_name} (schema {data.meta.schema_version})")

    # Validate content exists
    if data.content is None:
        logger.error("Cannot render: content is None. Run full pipeline first.")
        return 1

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save canonical JSON
    canonical_path = output_dir / "canonical.json"
    canonical_path.write_text(data.to_json(), encoding="utf-8")
    logger.info(f"Saved: {canonical_path}")

    if all_variants:
        # Render all template × variant combinations
        variants_dir = output_dir / "variants"
        variants_dir.mkdir(exist_ok=True)

        results = render_all_variants(data)
        for key, html in results.items():
            file_path = variants_dir / f"{key}.html"
            file_path.write_text(html, encoding="utf-8")
            logger.debug(f"Saved: {file_path}")

        # Also save default as index.html
        default_key = f"{data.render.template_type}_v{data.render.variant_id}"
        index_path = output_dir / "index.html"
        index_path.write_text(results.get(default_key, results[f"{data.render.template_type}_v0"]), encoding="utf-8")
        logger.info(f"Saved: {index_path}")

        logger.info(f"Rendered {len(results)} variants to {variants_dir}")

    else:
        # Render single page
        try:
            html = render_landing(data, template_override, variant_override)
        except PipelineError as e:
            logger.error(f"Render failed: {e}")
            return 1

        index_path = output_dir / "index.html"
        index_path.write_text(html, encoding="utf-8")
        logger.info(f"Saved: {index_path}")

    print(f"\n{'='*60}")
    print(f"OUTPUT: {output_dir}")
    print(f"{'='*60}")
    print(f"  canonical.json  - Source of truth")
    print(f"  index.html      - Rendered landing page")
    if all_variants:
        print(f"  variants/       - All {len(results)} template × variant combinations")

    return 0


def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0=success, 1=error)
    """
    args = parse_args()

    # Configure logging
    if args.quiet:
        level = logging.ERROR
    elif args.verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO

    configure_logging(level=level, format_style="simple")

    logger.debug(f"Schema version: {SCHEMA_VERSION}")

    # Resolve output directory
    output_dir = Path(args.output)

    try:
        if args.example:
            return run_example(args.example, output_dir)
        elif args.input:
            return run_render(
                input_path=Path(args.input),
                output_dir=output_dir,
                all_variants=args.all_variants,
                template_override=args.template,
                variant_override=args.variant,
            )
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        return 130
    except PipelineError as e:
        logger.error(f"Pipeline error: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
