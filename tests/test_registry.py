"""Tests for the SUMO Type Registry.

Tests cover:
- KIF parsing from Merge.kif
- Class hierarchy traversal (ancestors, children, descendants)
- Formal subsumption checks (is_subclass)
- Entity classification (EntityType -> SUMO concept)
- Keyword-based refinement
- Ontological distance computation
- Cache save/load roundtrip
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from sumo.registry import (
    SUMOHierarchy,
    SUMOTypeRegistry,
    parse_kif_hierarchy,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

# Minimal KIF content for unit tests (avoids depending on full Merge.kif)
MINIMAL_KIF = """\
;; Minimal SUMO hierarchy for testing

(subclass Physical Entity)
(subclass Abstract Entity)
(subclass Object Physical)
(subclass Process Physical)
(subclass Region Object)
(subclass SelfConnectedObject Object)
(subclass CorpuscularObject SelfConnectedObject)
(subclass ContentBearingPhysical Physical)
(subclass ContentBearingObject CorpuscularObject)
(subclass ContentBearingObject ContentBearingPhysical)
(subclass Organism SelfConnectedObject)
(subclass Agent Object)
(subclass AutonomousAgent Agent)
(subclass SentientAgent AutonomousAgent)
(subclass CognitiveAgent SentientAgent)
(subclass Human CognitiveAgent)
(subclass Human Hominid)
(subclass Hominid Primate)
(subclass Primate Mammal)
(subclass Mammal WarmBloodedVertebrate)
(subclass WarmBloodedVertebrate Vertebrate)
(subclass Vertebrate Animal)
(subclass Animal Organism)
(subclass Artifact CorpuscularObject)
(subclass Device Artifact)
(subclass Vehicle Device)
(subclass Automobile Vehicle)
(subclass Aircraft Vehicle)
(subclass WaterVehicle Vehicle)
(subclass Weapon Artifact)
(subclass Building StationaryArtifact)
(subclass StationaryArtifact Artifact)
(subclass Furniture Artifact)
(subclass Text LinguisticExpression)
(subclass LinguisticExpression ContentBearingPhysical)
(subclass ComputerProgram Procedure)
(subclass Procedure Process)
(subclass Quantity Abstract)
(subclass Attribute Abstract)
(subclass Proposition Abstract)
(subclass Relation Abstract)
(subclass Collection Physical)
(subclass Organization CognitiveAgent)
(subclass Organization Collection)
(subclass Corporation Organization)
(subclass EducationalOrganization Organization)
(subclass GovernmentOrganization Organization)
(subclass GeographicArea Region)
(subclass City GeopoliticalArea)
(subclass Nation GeopoliticalArea)
(subclass GeopoliticalArea GeographicArea)
(subclass LandArea Region)
(subclass WaterArea Region)
(subclass Database Artifact)
(subclass ComputerNetwork Artifact)
(subclass ComputerLanguage ArtificialLanguage)
(subclass ArtificialLanguage Language)
(subclass Language LinguisticExpression)
(subclass EngineeringComponent Device)

(documentation Entity EnglishLanguage "The universal class of individuals.")
(documentation Human EnglishLanguage "Homo sapiens.")
(documentation Vehicle EnglishLanguage "A device used primarily for transporting.")
(documentation Process EnglishLanguage "Something that happens over time.")
"""


@pytest.fixture
def minimal_kif_path(tmp_path: Path) -> Path:
    """Write minimal KIF to a temp file."""
    kif_file = tmp_path / "test_sumo.kif"
    kif_file.write_text(MINIMAL_KIF, encoding="utf-8")
    return kif_file


@pytest.fixture
def hierarchy(minimal_kif_path: Path) -> SUMOHierarchy:
    """Parse the minimal KIF into a hierarchy."""
    return parse_kif_hierarchy(minimal_kif_path)


@pytest.fixture
def registry(minimal_kif_path: Path) -> SUMOTypeRegistry:
    """Create a registry from the minimal KIF."""
    return SUMOTypeRegistry(kif_path=minimal_kif_path)


# ---------------------------------------------------------------------------
# KIF Parsing Tests
# ---------------------------------------------------------------------------


class TestKIFParsing:
    """Test SUO-KIF file parsing."""

    def test_parses_concepts(self, hierarchy: SUMOHierarchy) -> None:
        assert hierarchy.size > 0
        assert "Entity" in hierarchy.concepts
        assert "Physical" in hierarchy.concepts
        assert "Human" in hierarchy.concepts
        assert "Vehicle" in hierarchy.concepts

    def test_parses_parent_relationships(self, hierarchy: SUMOHierarchy) -> None:
        assert hierarchy.get_parent("Physical") == "Entity"
        assert hierarchy.get_parent("Abstract") == "Entity"
        assert hierarchy.get_parent("Object") == "Physical"
        assert hierarchy.get_parent("Automobile") == "Vehicle"

    def test_entity_is_root(self, hierarchy: SUMOHierarchy) -> None:
        assert hierarchy.get_parent("Entity") is None

    def test_parses_children(self, hierarchy: SUMOHierarchy) -> None:
        entity_children = hierarchy.get_children("Entity")
        assert "Physical" in entity_children
        assert "Abstract" in entity_children

    def test_parses_documentation(self, hierarchy: SUMOHierarchy) -> None:
        human = hierarchy.concepts.get("Human")
        assert human is not None
        assert "Homo sapiens" in human.description

    def test_handles_multiple_parents(self, hierarchy: SUMOHierarchy) -> None:
        # Human has both (subclass Human CognitiveAgent) and (subclass Human Hominid)
        # First one (CognitiveAgent) should be the primary parent
        assert hierarchy.get_parent("Human") == "CognitiveAgent"

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            parse_kif_hierarchy(tmp_path / "nonexistent.kif")


# ---------------------------------------------------------------------------
# Hierarchy Traversal Tests
# ---------------------------------------------------------------------------


class TestHierarchyTraversal:
    """Test hierarchy navigation methods."""

    def test_get_ancestors(self, hierarchy: SUMOHierarchy) -> None:
        ancestors = hierarchy.get_ancestors("Automobile")
        assert ancestors[0] == "Automobile"
        assert "Vehicle" in ancestors
        assert "Device" in ancestors
        assert "Artifact" in ancestors
        assert ancestors[-1] == "Entity"

    def test_get_ancestors_root(self, hierarchy: SUMOHierarchy) -> None:
        ancestors = hierarchy.get_ancestors("Entity")
        assert ancestors == ["Entity"]

    def test_get_ancestors_unknown(self, hierarchy: SUMOHierarchy) -> None:
        assert hierarchy.get_ancestors("NonExistentConcept") == []

    def test_get_depth(self, hierarchy: SUMOHierarchy) -> None:
        assert hierarchy.get_depth("Entity") == 0
        assert hierarchy.get_depth("Physical") == 1
        assert hierarchy.get_depth("Object") == 2
        assert hierarchy.get_depth("Automobile") > 3

    def test_get_depth_unknown(self, hierarchy: SUMOHierarchy) -> None:
        assert hierarchy.get_depth("FakeConceptXYZ") == -1

    def test_get_all_descendants(self, hierarchy: SUMOHierarchy) -> None:
        vehicle_descendants = hierarchy.get_all_descendants("Vehicle")
        assert "Automobile" in vehicle_descendants
        assert "Aircraft" in vehicle_descendants
        assert "WaterVehicle" in vehicle_descendants
        assert "Vehicle" not in vehicle_descendants


# ---------------------------------------------------------------------------
# Subsumption Tests
# ---------------------------------------------------------------------------


class TestSubsumption:
    """Test formal subsumption (is_subclass) checks."""

    def test_same_concept(self, hierarchy: SUMOHierarchy) -> None:
        assert hierarchy.is_subclass("Human", "Human") is True

    def test_direct_subclass(self, hierarchy: SUMOHierarchy) -> None:
        assert hierarchy.is_subclass("Physical", "Entity") is True
        assert hierarchy.is_subclass("Object", "Physical") is True

    def test_transitive_subclass(self, hierarchy: SUMOHierarchy) -> None:
        assert hierarchy.is_subclass("Human", "Entity") is True
        assert hierarchy.is_subclass("Automobile", "Physical") is True

    def test_not_subclass(self, hierarchy: SUMOHierarchy) -> None:
        assert hierarchy.is_subclass("Entity", "Human") is False
        assert hierarchy.is_subclass("Automobile", "Human") is False
        assert hierarchy.is_subclass("Process", "Object") is False

    def test_unknown_concept(self, hierarchy: SUMOHierarchy) -> None:
        assert hierarchy.is_subclass("FakeThing", "Entity") is False
        assert hierarchy.is_subclass("Human", "FakeThing") is False

    def test_common_ancestor(self, hierarchy: SUMOHierarchy) -> None:
        common = hierarchy.get_common_ancestor("Human", "Organization")
        assert common == "CognitiveAgent"

        common = hierarchy.get_common_ancestor("Automobile", "Aircraft")
        assert common == "Vehicle"

    def test_common_ancestor_same(self, hierarchy: SUMOHierarchy) -> None:
        assert hierarchy.get_common_ancestor("Human", "Human") == "Human"


# ---------------------------------------------------------------------------
# Classification Tests
# ---------------------------------------------------------------------------


class TestClassification:
    """Test entity-to-SUMO classification."""

    def test_default_person_mapping(self, registry: SUMOTypeRegistry) -> None:
        assert registry.classify("person", "John Doe") == "Human"

    def test_default_organization_mapping(self, registry: SUMOTypeRegistry) -> None:
        assert registry.classify("organization", "Acme Inc") == "Corporation"
        assert registry.classify("organization", "The Alliance") == "Organization"

    def test_default_location_mapping(self, registry: SUMOTypeRegistry) -> None:
        assert registry.classify("location", "New York") == "GeographicArea"

    def test_default_event_mapping(self, registry: SUMOTypeRegistry) -> None:
        assert registry.classify("event", "Product Launch") == "Process"

    def test_default_agent_mapping(self, registry: SUMOTypeRegistry) -> None:
        assert registry.classify("agent", "aria-01") == "CognitiveAgent"

    def test_keyword_refinement_software(self, registry: SUMOTypeRegistry) -> None:
        result = registry.classify("technology", "PostgreSQL database software")
        assert result == "Database"

    def test_keyword_refinement_vehicle(self, registry: SUMOTypeRegistry) -> None:
        result = registry.classify("technology", "Tesla Model 3 automobile")
        assert result == "Automobile"

    def test_keyword_refinement_org_type(self, registry: SUMOTypeRegistry) -> None:
        result = registry.classify("organization", "MIT university")
        assert result == "EducationalOrganization"

    def test_unknown_entity_type(self, registry: SUMOTypeRegistry) -> None:
        assert registry.classify("nonexistent_type", "Something") == "Entity"

    def test_case_insensitive(self, registry: SUMOTypeRegistry) -> None:
        assert registry.classify("PERSON", "Alice") == "Human"
        assert registry.classify("Person", "Bob") == "Human"

    def test_subsumption_via_registry(self, registry: SUMOTypeRegistry) -> None:
        assert registry.is_subclass("Human", "CognitiveAgent") is True
        assert registry.is_subclass("Automobile", "Artifact") is True
        assert registry.is_subclass("Process", "Object") is False


# ---------------------------------------------------------------------------
# Ontological Distance Tests
# ---------------------------------------------------------------------------


class TestOntologicalDistance:
    """Test formal ontological distance computation."""

    def test_same_concept_distance(self, registry: SUMOTypeRegistry) -> None:
        assert registry.get_ontological_distance("Human", "Human") == 0

    def test_parent_child_distance(self, registry: SUMOTypeRegistry) -> None:
        assert registry.get_ontological_distance("Physical", "Entity") == 1

    def test_sibling_distance(self, registry: SUMOTypeRegistry) -> None:
        assert registry.get_ontological_distance("Physical", "Abstract") == 2

    def test_unknown_concept_distance(self, registry: SUMOTypeRegistry) -> None:
        assert registry.get_ontological_distance("Human", "FakeThing") == -1


# ---------------------------------------------------------------------------
# Cache Tests
# ---------------------------------------------------------------------------


class TestCaching:
    """Test JSON cache save/load roundtrip."""

    def test_cache_roundtrip(self, minimal_kif_path: Path, tmp_path: Path) -> None:
        cache_path = tmp_path / "sumo_cache.json"

        reg1 = SUMOTypeRegistry(kif_path=minimal_kif_path, cache_path=cache_path)
        _ = reg1.hierarchy
        assert cache_path.exists()

        reg2 = SUMOTypeRegistry(kif_path=minimal_kif_path, cache_path=cache_path)
        h2 = reg2.hierarchy

        assert h2.size == reg1.hierarchy.size
        assert h2.is_subclass("Human", "CognitiveAgent")
        assert h2.get_parent("Physical") == "Entity"

    def test_cache_is_valid_json(self, minimal_kif_path: Path, tmp_path: Path) -> None:
        cache_path = tmp_path / "sumo_cache.json"
        reg = SUMOTypeRegistry(kif_path=minimal_kif_path, cache_path=cache_path)
        _ = reg.hierarchy

        with open(cache_path) as f:
            data = json.load(f)

        assert "concepts" in data
        assert "children" in data
        assert "Entity" in data["concepts"]


# ---------------------------------------------------------------------------
# Integration with Real Merge.kif (if available)
# ---------------------------------------------------------------------------


class TestRealSUMO:
    """Tests against the actual SUMO Merge.kif (skipped if not available)."""

    MERGE_KIF = Path(__file__).resolve().parent.parent / "data" / "Merge.kif"

    @pytest.fixture(autouse=True)
    def _skip_if_no_sumo(self) -> None:
        if not self.MERGE_KIF.exists():
            pytest.skip("SUMO Merge.kif not available")

    def test_loads_real_hierarchy(self) -> None:
        hierarchy = parse_kif_hierarchy(self.MERGE_KIF)
        assert hierarchy.size > 500

    def test_real_human_ancestry(self) -> None:
        registry = SUMOTypeRegistry(kif_path=self.MERGE_KIF)
        ancestors = registry.get_ancestors("Human")
        assert ancestors[0] == "Human"
        assert "Entity" in ancestors
        assert len(ancestors) > 3

    def test_real_subsumption(self) -> None:
        registry = SUMOTypeRegistry(kif_path=self.MERGE_KIF)
        assert registry.is_subclass("Human", "Entity")
        assert registry.is_subclass("Object", "Physical")
        assert registry.is_subclass("Process", "Physical")
        assert not registry.is_subclass("Process", "Object")
