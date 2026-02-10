"""Tests for the Ontology Namespace Resolver."""

from __future__ import annotations

from pathlib import Path

import pytest

from sumo.namespace_resolver import OntologyNamespaceResolver
from sumo.registry import SUMOTypeRegistry

# Reuse the minimal KIF from test_registry
MINIMAL_KIF = """\
(subclass Physical Entity)
(subclass Abstract Entity)
(subclass Object Physical)
(subclass Process Physical)
(subclass Region Object)
(subclass SelfConnectedObject Object)
(subclass CorpuscularObject SelfConnectedObject)
(subclass Organism SelfConnectedObject)
(subclass Agent Object)
(subclass AutonomousAgent Agent)
(subclass SentientAgent AutonomousAgent)
(subclass CognitiveAgent SentientAgent)
(subclass Human CognitiveAgent)
(subclass Artifact CorpuscularObject)
(subclass Device Artifact)
(subclass Vehicle Device)
(subclass Automobile Vehicle)
(subclass Aircraft Vehicle)
(subclass WaterVehicle Vehicle)
(subclass Building StationaryArtifact)
(subclass StationaryArtifact Artifact)
(subclass Organization CognitiveAgent)
(subclass Corporation Organization)
(subclass GeographicArea Region)
(subclass City GeopoliticalArea)
(subclass GeopoliticalArea GeographicArea)
(subclass Database Artifact)
(subclass ComputerProgram Procedure)
(subclass Procedure Process)
(subclass Collection Physical)
"""


@pytest.fixture
def resolver(tmp_path: Path) -> OntologyNamespaceResolver:
    kif_file = tmp_path / "test.kif"
    kif_file.write_text(MINIMAL_KIF, encoding="utf-8")
    registry = SUMOTypeRegistry(kif_path=kif_file)
    return OntologyNamespaceResolver(registry)


@pytest.fixture
def registry(tmp_path: Path) -> SUMOTypeRegistry:
    kif_file = tmp_path / "test.kif"
    kif_file.write_text(MINIMAL_KIF, encoding="utf-8")
    return SUMOTypeRegistry(kif_path=kif_file)


class TestGenerateAriaId:
    """Test aria:* ID generation from SUMO concepts."""

    def test_automobile(
        self, resolver: OntologyNamespaceResolver, registry: SUMOTypeRegistry
    ) -> None:
        concept = registry.get_concept_info("Automobile")
        assert concept is not None
        aria_id = resolver.generate_aria_id(concept)
        # Should contain path segments from Object down to Automobile
        assert aria_id.startswith("aria:EntityType/")
        assert "Vehicle" in aria_id
        assert aria_id.endswith("/Automobile")

    def test_human_uses_alias(
        self, resolver: OntologyNamespaceResolver, registry: SUMOTypeRegistry
    ) -> None:
        concept = registry.get_concept_info("Human")
        assert concept is not None
        aria_id = resolver.generate_aria_id(concept)
        # Human -> Person via alias
        assert aria_id.endswith("/Person")

    def test_corporation_uses_alias(
        self, resolver: OntologyNamespaceResolver, registry: SUMOTypeRegistry
    ) -> None:
        concept = registry.get_concept_info("Corporation")
        assert concept is not None
        aria_id = resolver.generate_aria_id(concept)
        # Corporation -> Organization via alias
        assert "Organization" in aria_id

    def test_strips_abstract_roots(
        self, resolver: OntologyNamespaceResolver, registry: SUMOTypeRegistry
    ) -> None:
        concept = registry.get_concept_info("Vehicle")
        assert concept is not None
        aria_id = resolver.generate_aria_id(concept)
        # The path portion (after "aria:EntityType/") should NOT contain
        # Entity or Physical as standalone segments
        path = aria_id.removeprefix("aria:EntityType/")
        segments = path.split("/")
        assert "Entity" not in segments
        assert "Physical" not in segments

    def test_process_concept(
        self, resolver: OntologyNamespaceResolver, registry: SUMOTypeRegistry
    ) -> None:
        concept = registry.get_concept_info("ComputerProgram")
        assert concept is not None
        aria_id = resolver.generate_aria_id(concept)
        assert aria_id.startswith("aria:EntityType/")
        assert aria_id.endswith("/ComputerProgram")


class TestReverseLookup:
    """Test reverse resolution from aria:* to SUMO."""

    def test_resolve_person_to_human(self, resolver: OntologyNamespaceResolver) -> None:
        result = resolver.resolve_sumo_from_aria("aria:EntityType/Object/Agent/Person")
        assert result == "Human"

    def test_resolve_direct_sumo_name(self, resolver: OntologyNamespaceResolver) -> None:
        result = resolver.resolve_sumo_from_aria("aria:EntityType/Object/Artifact/Vehicle")
        assert result == "Vehicle"

    def test_resolve_unknown_returns_none(self, resolver: OntologyNamespaceResolver) -> None:
        result = resolver.resolve_sumo_from_aria("aria:EntityType/Object/FakeThing")
        assert result is None

    def test_non_entity_type_returns_none(self, resolver: OntologyNamespaceResolver) -> None:
        result = resolver.resolve_sumo_from_aria("aria:Domain/NLP/NER")
        assert result is None

    def test_resolve_organization_alias(self, resolver: OntologyNamespaceResolver) -> None:
        result = resolver.resolve_sumo_from_aria("aria:EntityType/Object/Agent/Organization")
        # "Organization" is a reverse alias for "Corporation", but Organization
        # is also a direct SUMO concept. Should resolve to the direct concept.
        assert result == "Organization"
