"""CLI tool: parse Merge.kif and generate a JSON hierarchy cache.

Usage::

    python -m sumo.build_cache --kif data/Merge.kif --output sumo/data/sumo_hierarchy_v1.json
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from sumo.registry import SUMO_CACHE_FILENAME, parse_kif_hierarchy

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Parse SUMO Merge.kif and generate JSON hierarchy cache.",
    )
    parser.add_argument(
        "--kif",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "data" / "Merge.kif",
        help="Path to the SUMO Merge.kif file",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parent / "data" / SUMO_CACHE_FILENAME,
        help="Output path for the JSON cache",
    )
    args = parser.parse_args(argv)

    if not args.kif.exists():
        logger.error("KIF file not found: %s", args.kif)
        logger.error("Run 'make download-kif' to fetch Merge.kif from the Ontology Portal.")
        sys.exit(1)

    hierarchy = parse_kif_hierarchy(args.kif)

    data = {
        "version": "1",
        "source": str(args.kif.name),
        "concept_count": hierarchy.size,
        "concepts": {
            name: {
                "parent": c.parent,
                "description": c.description,
            }
            for name, c in hierarchy.concepts.items()
        },
        "children": hierarchy.children,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(data, f, indent=None, separators=(",", ":"))

    logger.info(
        "Wrote %d concepts to %s (%.1f MB)",
        hierarchy.size,
        args.output,
        args.output.stat().st_size / 1_048_576,
    )


if __name__ == "__main__":
    main()
