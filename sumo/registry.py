"""SUMO Type Registry — Formal ontology grounding for knowledge graph entities.

Loads the SUMO (Suggested Upper Merged Ontology) class hierarchy from SUO-KIF
files and provides mapping from informal entity types to formally axiomatized
SUMO concepts.

This module is purely additive — it enriches entities with a ``sumo_type``
property alongside existing EntityType labels. No existing behavior is modified.

See Also:
    - SUMO: https://www.ontologyportal.org
    - SUO-KIF spec: http://www.ontologyportal.org
    - Niles & Pease (2001), "Towards a Standard Upper Ontology", FOIS-2001
"""

from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------

# Versioned cache filename — bump when Merge.kif or parser changes
SUMO_CACHE_VERSION = "v1"
SUMO_CACHE_FILENAME = f"sumo_hierarchy_{SUMO_CACHE_VERSION}.json"

# Resolution order for KIF source:
# 1. SUMO_KIF_PATH env var (explicit override for any tier)
# 2. data/Merge.kif at repo root (local dev)
_DEFAULT_KIF_PATH = Path(
    os.environ.get(
        "SUMO_KIF_PATH",
        str(Path(__file__).resolve().parent.parent / "data" / "Merge.kif"),
    )
)

# Resolution order for JSON cache:
# 1. SUMO_CACHE_PATH env var (explicit override for any tier)
# 2. sumo/data/sumo_hierarchy_v1.json inside the installed package
_DEFAULT_CACHE_PATH: Path | None = (
    Path(os.environ["SUMO_CACHE_PATH"])
    if "SUMO_CACHE_PATH" in os.environ
    else Path(__file__).resolve().parent / "data" / SUMO_CACHE_FILENAME
)

# Regex to extract (subclass Child Parent) assertions from SUO-KIF
_SUBCLASS_PATTERN = re.compile(r"^\(subclass\s+(\S+)\s+(\S+)\)")

# Regex to extract (documentation Concept Language "text") for descriptions
_DOC_PATTERN = re.compile(r'^\(documentation\s+(\S+)\s+EnglishLanguage\s+"([^"]*)')


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SUMOConcept:
    """A concept in the SUMO class hierarchy.

    Attributes:
        name: The SUMO concept name (e.g., 'Human', 'Vehicle', 'Process').
        parent: The direct parent concept name, or None for 'Entity' (the root).
        description: English documentation string from SUMO, if available.
    """

    name: str
    parent: str | None = None
    description: str = ""


@dataclass
class SUMOHierarchy:
    """The parsed SUMO class hierarchy.

    Provides O(1) parent lookup, O(depth) ancestor traversal, and
    O(1) subsumption checking (after one-time precomputation).
    """

    concepts: dict[str, SUMOConcept] = field(default_factory=dict)
    children: dict[str, list[str]] = field(default_factory=dict)
    _ancestor_cache: dict[str, frozenset[str]] = field(default_factory=dict, repr=False)

    @property
    def size(self) -> int:
        """Number of concepts in the hierarchy."""
        return len(self.concepts)

    def get_parent(self, concept: str) -> str | None:
        """Get the direct parent of a concept."""
        c = self.concepts.get(concept)
        return c.parent if c else None

    def get_children(self, concept: str) -> list[str]:
        """Get direct children of a concept."""
        return self.children.get(concept, [])

    def get_ancestors(self, concept: str) -> list[str]:
        """Get all ancestors from concept to root (inclusive of concept).

        Returns:
            List from concept up to root,
            e.g. ``['Human', 'CognitiveAgent', ..., 'Entity']``.
        """
        if concept not in self.concepts:
            return []
        ancestors: list[str] = []
        current: str | None = concept
        visited: set[str] = set()
        while current and current not in visited:
            ancestors.append(current)
            visited.add(current)
            current = self.get_parent(current)
        return ancestors

    def get_ancestor_set(self, concept: str) -> frozenset[str]:
        """Get the set of all ancestors (cached for repeated subsumption checks)."""
        if concept not in self._ancestor_cache:
            self._ancestor_cache[concept] = frozenset(self.get_ancestors(concept))
        return self._ancestor_cache[concept]

    def is_subclass(self, child: str, parent: str) -> bool:
        """Check if *child* is a subclass of *parent* (formal subsumption).

        This is provable from SUMO axioms::

            (=> (and (subclass ?X ?Y) (instance ?Z ?X)) (instance ?Z ?Y))
        """
        if child == parent:
            return True
        if child not in self.concepts or parent not in self.concepts:
            return False
        return parent in self.get_ancestor_set(child)

    def get_common_ancestor(self, concept_a: str, concept_b: str) -> str | None:
        """Find the most specific common ancestor of two concepts."""
        ancestors_a = self.get_ancestors(concept_a)
        ancestors_b_set = self.get_ancestor_set(concept_b)

        for ancestor in ancestors_a:
            if ancestor in ancestors_b_set:
                return ancestor
        return None

    def get_depth(self, concept: str) -> int:
        """Get the depth of a concept in the hierarchy (root = 0).

        Returns -1 if concept not found.
        """
        if concept not in self.concepts:
            return -1
        return len(self.get_ancestors(concept)) - 1

    def get_all_descendants(self, concept: str) -> list[str]:
        """Get all descendants of a concept (for subsumption-based query expansion).

        The concept itself is **not** included in the result.
        """
        descendants: list[str] = []
        stack = list(self.get_children(concept))
        visited: set[str] = set()
        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)
            descendants.append(current)
            stack.extend(self.get_children(current))
        return descendants


# ---------------------------------------------------------------------------
# KIF parser
# ---------------------------------------------------------------------------


def parse_kif_hierarchy(kif_path: Path) -> SUMOHierarchy:
    """Parse SUMO class hierarchy from a SUO-KIF file.

    Extracts ``(subclass Child Parent)`` assertions and optionally
    ``(documentation Concept EnglishLanguage "...")`` descriptions.

    Args:
        kif_path: Path to the .kif file (typically ``Merge.kif``).

    Raises:
        FileNotFoundError: If the KIF file doesn't exist.
    """
    if not kif_path.exists():
        raise FileNotFoundError(f"SUMO KIF file not found: {kif_path}")

    hierarchy = SUMOHierarchy()
    descriptions: dict[str, str] = {}
    subclass_pairs: list[tuple[str, str]] = []

    logger.info("Parsing SUMO hierarchy from %s", kif_path)

    with open(kif_path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()

            # Skip comments and empty lines
            if not line or line.startswith(";"):
                continue

            # Extract subclass assertions
            match = _SUBCLASS_PATTERN.match(line)
            if match:
                child, parent = match.group(1), match.group(2)
                subclass_pairs.append((child, parent))
                continue

            # Extract documentation (first line only — multi-line docs truncated)
            doc_match = _DOC_PATTERN.match(line)
            if doc_match:
                concept_name = doc_match.group(1)
                doc_text = doc_match.group(2)
                doc_text = doc_text.replace("&%", "").strip()
                if concept_name not in descriptions:
                    descriptions[concept_name] = doc_text

    # Build hierarchy from subclass assertions.
    # SUMO allows multiple parents (multiple inheritance).
    # We take the first ``(subclass X Y)`` assertion as the primary parent.
    primary_parent: dict[str, str] = {}
    for child, parent in subclass_pairs:
        if child not in primary_parent:
            primary_parent[child] = parent

    all_concepts: set[str] = set()
    for child, parent in subclass_pairs:
        all_concepts.add(child)
        all_concepts.add(parent)

    for concept_name in all_concepts:
        hierarchy.concepts[concept_name] = SUMOConcept(
            name=concept_name,
            parent=primary_parent.get(concept_name),
            description=descriptions.get(concept_name, ""),
        )
        parent = primary_parent.get(concept_name)
        if parent:
            if parent not in hierarchy.children:
                hierarchy.children[parent] = []
            hierarchy.children[parent].append(concept_name)

    # Ensure Entity exists as root
    if "Entity" not in hierarchy.concepts:
        hierarchy.concepts["Entity"] = SUMOConcept(
            name="Entity",
            description="The universal class of individuals.",
        )

    logger.info(
        "Parsed SUMO hierarchy: %d concepts, %d subclass assertions",
        len(hierarchy.concepts),
        len(subclass_pairs),
    )

    return hierarchy


# ---------------------------------------------------------------------------
# Default EntityType → SUMO concept mapping
# ---------------------------------------------------------------------------

_DEFAULT_ENTITY_TYPE_MAP: dict[str, str] = {
    # Standard RAG entities
    "document": "Text",
    "chunk": "Text",
    "person": "Human",
    "organization": "Organization",
    "location": "GeographicArea",
    "concept": "Abstract",
    "technology": "EngineeringComponent",
    "event": "Process",
    # Trace Manifold entities
    "agent_trace": "ContentBearingObject",
    "conversation": "ContentBearingObject",
    "code_change": "Process",
    "tool_execution": "Process",
    "memory_episodic": "ContentBearingObject",
    "memory_semantic": "Proposition",
    "workspace": "Collection",
    "agent": "CognitiveAgent",
}

# Keyword-based refinement: if the entity name contains any of these
# keywords, override the default SUMO type with a more specific one.
_NAME_KEYWORD_REFINEMENTS: list[tuple[list[str], str]] = [
    # People & agents
    (["doctor", "physician", "nurse", "surgeon"], "Human"),
    (["company", "corp", "inc", "ltd", "llc"], "Corporation"),
    (["university", "college", "school", "institute"], "EducationalOrganization"),
    (
        ["government", "ministry", "agency", "department"],
        "GovernmentOrganization",
    ),
    # Technology
    (["database", "datastore"], "Database"),
    (["software", "program", "application", "app"], "ComputerProgram"),
    (["algorithm", "function", "method", "procedure"], "Procedure"),
    (["server", "computer", "machine", "device"], "Device"),
    (["network", "internet", "web"], "ComputerNetwork"),
    (
        ["language", "python", "javascript", "typescript", "go", "rust", "java"],
        "ComputerLanguage",
    ),
    # Vehicles & artifacts
    (["car", "automobile", "sedan", "truck"], "Automobile"),
    (["aircraft", "airplane", "plane", "jet"], "Aircraft"),
    (["ship", "boat", "vessel"], "WaterVehicle"),
    (["vehicle", "transport"], "Vehicle"),
    (["weapon", "missile", "gun"], "Weapon"),
    (["building", "tower", "house", "office"], "Building"),
    # Science
    (["protein", "enzyme", "amino acid"], "Protein"),
    (["molecule", "compound", "chemical"], "CompoundSubstance"),
    (["cell", "neuron", "tissue"], "Cell"),
    (["gene", "dna", "rna", "genome"], "Gene"),
    # Locations
    (["city", "town", "village"], "City"),
    (["country", "nation", "state"], "Nation"),
    (["ocean", "sea", "lake", "river"], "WaterArea"),
    (["mountain", "hill", "peak"], "LandArea"),
    # Processes
    (["war", "battle", "conflict", "attack"], "ViolentContest"),
    (["meeting", "conference", "summit"], "Meeting"),
    (["election", "vote", "referendum"], "Election"),
    (["experiment", "trial", "study"], "Experiment"),
]


# ---------------------------------------------------------------------------
# SUMOTypeRegistry
# ---------------------------------------------------------------------------


class SUMOTypeRegistry:
    """Registry for mapping entities to SUMO concepts.

    Loads the SUMO class hierarchy once and provides fast classification
    of entities based on their EntityType and name.

    Usage::

        registry = SUMOTypeRegistry()
        sumo_type = registry.classify("person", "Dr. Jane Smith")
        # Returns "Human"

        sumo_type = registry.classify("technology", "PostgreSQL database")
        # Returns "Database"

        # Hierarchy queries
        registry.is_subclass("Human", "CognitiveAgent")  # True
        registry.get_ancestors("Human")  # ['Human', 'Primate', ..., 'Entity']
    """

    def __init__(
        self,
        kif_path: Path | str | None = None,
        cache_path: Path | str | None = None,
    ) -> None:
        self._kif_path = Path(kif_path) if kif_path else _DEFAULT_KIF_PATH
        self._cache_path = Path(cache_path) if cache_path else _DEFAULT_CACHE_PATH
        self._hierarchy: SUMOHierarchy | None = None
        self._loaded = False

    @property
    def hierarchy(self) -> SUMOHierarchy:
        """Lazy-load the hierarchy on first access."""
        if not self._loaded:
            self._load()
        assert self._hierarchy is not None
        return self._hierarchy

    def _load(self) -> None:
        """Load the SUMO hierarchy from cache or KIF file."""
        if (
            self._cache_path
            and self._cache_path.exists()
            and (
                not self._kif_path.exists()
                or self._cache_path.stat().st_mtime > self._kif_path.stat().st_mtime
            )
        ):
            self._load_from_cache()
            self._loaded = True
            return

        # Parse from KIF
        self._hierarchy = parse_kif_hierarchy(self._kif_path)
        self._loaded = True

        # Save cache for next time
        if self._cache_path:
            self._save_cache()

    def _load_from_cache(self) -> None:
        """Load hierarchy from JSON cache."""
        assert self._cache_path is not None
        logger.info("Loading SUMO hierarchy from cache: %s", self._cache_path)

        with open(self._cache_path) as f:
            data = json.load(f)

        hierarchy = SUMOHierarchy()
        for name, info in data["concepts"].items():
            hierarchy.concepts[name] = SUMOConcept(
                name=name,
                parent=info.get("parent"),
                description=info.get("description", ""),
            )
        hierarchy.children = dict(data.get("children", {}))

        self._hierarchy = hierarchy
        logger.info("Loaded %d concepts from cache", hierarchy.size)

    def _save_cache(self) -> None:
        """Save hierarchy to JSON cache."""
        assert self._cache_path is not None and self._hierarchy is not None

        data = {
            "concepts": {
                name: {
                    "parent": c.parent,
                    "description": c.description,
                }
                for name, c in self._hierarchy.concepts.items()
            },
            "children": self._hierarchy.children,
        }

        self._cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._cache_path, "w") as f:
            json.dump(data, f, indent=None, separators=(",", ":"))

        logger.info("Saved SUMO hierarchy cache: %s", self._cache_path)

    def classify(
        self,
        entity_type: str,
        entity_name: str = "",
        _context: str = "",
    ) -> str:
        """Classify an entity to a SUMO concept.

        Uses a two-stage approach:

        1. Look up default mapping for *entity_type*
        2. Try to refine based on *entity_name* keywords

        Returns:
            SUMO concept name (e.g., ``"Human"``, ``"ComputerProgram"``).
            Falls back to ``"Entity"`` if no mapping found.
        """
        entity_type_lower = entity_type.lower().strip()
        sumo_type = _DEFAULT_ENTITY_TYPE_MAP.get(entity_type_lower, "Entity")

        if entity_name:
            name_lower = entity_name.lower()
            for keywords, refined_type in _NAME_KEYWORD_REFINEMENTS:
                if any(kw in name_lower for kw in keywords):
                    if refined_type in self.hierarchy.concepts:
                        sumo_type = refined_type
                    break

        if sumo_type not in self.hierarchy.concepts:
            logger.debug(
                "SUMO type '%s' not found in hierarchy for entity '%s' "
                "(type=%s), falling back to 'Entity'",
                sumo_type,
                entity_name,
                entity_type,
            )
            sumo_type = "Entity"

        return sumo_type

    # ------------------------------------------------------------------
    # Convenience wrappers
    # ------------------------------------------------------------------

    def is_subclass(self, child: str, parent: str) -> bool:
        """Check formal subsumption between two SUMO concepts."""
        return self.hierarchy.is_subclass(child, parent)

    def get_ancestors(self, concept: str) -> list[str]:
        """Get the full ancestry chain from concept to root."""
        return self.hierarchy.get_ancestors(concept)

    def get_descendants(self, concept: str) -> list[str]:
        """Get all descendants for subsumption-based query expansion."""
        return self.hierarchy.get_all_descendants(concept)

    def concept_exists(self, concept: str) -> bool:
        """Check if a concept exists in the SUMO hierarchy."""
        return concept in self.hierarchy.concepts

    def get_concept_info(self, concept: str) -> SUMOConcept | None:
        """Get full concept information."""
        return self.hierarchy.concepts.get(concept)

    def get_ontological_distance(self, concept_a: str, concept_b: str) -> int:
        """Compute formal ontological distance between two concepts.

        Distance is the sum of depths from each concept to their most
        specific common ancestor.

        Returns:
            Distance (0 if same concept, -1 if no common ancestor).
        """
        if concept_a == concept_b:
            return 0

        common = self.hierarchy.get_common_ancestor(concept_a, concept_b)
        if common is None:
            return -1

        depth_a = self.hierarchy.get_depth(concept_a)
        depth_b = self.hierarchy.get_depth(concept_b)
        depth_common = self.hierarchy.get_depth(common)

        return (depth_a - depth_common) + (depth_b - depth_common)
