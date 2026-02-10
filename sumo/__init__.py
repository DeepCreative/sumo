"""SUMO — Shared library for Suggested Upper Merged Ontology integration.

Provides formal ontology grounding for entity typing across the
Bravo Zero cognitive architecture.
"""

from sumo.registry import (
    SUMOConcept,
    SUMOHierarchy,
    SUMOTypeRegistry,
    parse_kif_hierarchy,
)

__all__ = [
    "SUMOConcept",
    "SUMOHierarchy",
    "SUMOTypeRegistry",
    "parse_kif_hierarchy",
]

__version__ = "0.1.0"
