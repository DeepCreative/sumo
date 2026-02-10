"""Ontology Namespace Resolver — derives ``aria:*`` IDs from SUMO concepts.

Makes the ``aria:EntityType/*`` namespace a **derived projection** of SUMO
rather than an independently maintained taxonomy. New entity types that SUMO
can classify get ``aria:*`` IDs automatically without manual mapping table
updates.

See Also:
    ADR-145 and architecture/sumo-formal-ontology-layer.md for the full design.
"""

from __future__ import annotations

import logging

from sumo.registry import SUMOConcept, SUMOTypeRegistry

logger = logging.getLogger(__name__)


class OntologyNamespaceResolver:
    """Derives ``aria:*`` namespace IDs from SUMO concept ancestry.

    Usage::

        from sumo import SUMOTypeRegistry
        from sumo.namespace_resolver import OntologyNamespaceResolver

        registry = SUMOTypeRegistry(cache_path="data/sumo_hierarchy.json")
        resolver = OntologyNamespaceResolver(registry)

        concept = registry.get_concept_info("Automobile")
        aria_id = resolver.generate_aria_id(concept)
        # -> "aria:EntityType/Object/Artifact/Device/Vehicle/Automobile"

        sumo_name = resolver.resolve_sumo_from_aria("aria:EntityType/Person")
        # -> "Human"  (via reverse alias lookup)
    """

    # Small alias table for cases where aria path segments use different
    # names than SUMO concepts. Most SUMO concepts map 1:1.
    ALIASES: dict[str, str] = {
        "Human": "Person",
        "Corporation": "Organization",
        "GeographicArea": "Location",
        "NationState": "Country",
        "GeopoliticalArea": "Region",
        "FinancialTransaction": "Transaction",
        "ContentBearingObject": "Content",
        "SelfConnectedObject": "PhysicalObject",
        "CorpuscularObject": "DiscreteObject",
    }

    # Concepts that are too abstract to include in the aria:* path.
    # Stripped from the ancestry before generating the ID.
    _ABSTRACT_ROOTS = frozenset({"Entity", "Physical", "Abstract"})

    def __init__(self, registry: SUMOTypeRegistry) -> None:
        self._registry = registry
        self._reverse_aliases: dict[str, str] = {v: k for k, v in self.ALIASES.items()}

    def generate_aria_id(self, concept: SUMOConcept) -> str:
        """Generate an ``aria:EntityType/*`` ID from a SUMO concept.

        The ID encodes the SUMO ancestry path, with aliases applied
        where ``aria:*`` conventions differ from SUMO naming.

        Example::

            SUMO concept "Automobile" with ancestry
            [Automobile, Vehicle, Device, Artifact, CorpuscularObject,
             SelfConnectedObject, Object, Physical, Entity]

            Produces: aria:EntityType/Object/DiscreteObject/Artifact/Device/Vehicle/Automobile

            (Entity and Physical are stripped as too abstract)
        """
        ancestors = self._registry.hierarchy.get_ancestors(concept.name)

        # Build path from Object/Abstract downward (skip Entity, Physical, Abstract)
        path_concepts: list[str] = []
        recording = False
        for anc in reversed(ancestors):  # root-to-leaf order
            if anc in self._ABSTRACT_ROOTS:
                continue
            recording = True
            if recording:
                path_concepts.append(anc)

        if not path_concepts:
            # Concept is at or above Object/Abstract — use just the name
            aliased = self.ALIASES.get(concept.name, concept.name)
            return f"aria:EntityType/{aliased}"

        # Apply aliases to each segment
        path_segments = [self.ALIASES.get(name, name) for name in path_concepts]

        return f"aria:EntityType/{'/'.join(path_segments)}"

    def resolve_sumo_from_aria(self, aria_id: str) -> str | None:
        """Reverse lookup: given an ``aria:*`` ID, find the SUMO concept.

        Uses the leaf segment and reverse-alias lookup.

        Returns:
            SUMO concept name, or ``None`` if not resolvable.
        """
        if not aria_id.startswith("aria:EntityType/"):
            return None

        leaf = aria_id.rstrip("/").split("/")[-1]

        # First check if the leaf is already a direct SUMO concept name
        if self._registry.concept_exists(leaf):
            return leaf

        # If not, try reverse alias lookup
        sumo_name = self._reverse_aliases.get(leaf)
        if sumo_name and self._registry.concept_exists(sumo_name):
            return sumo_name

        return None
