# sumo

Shared library for [SUMO (Suggested Upper Merged Ontology)](https://www.ontologyportal.org) integration in the Bravo Zero cognitive architecture.

Provides formal ontology grounding for entity typing across Carousel, d3n-core, and other services.

## Quick start

```bash
make install-dev
make download-kif   # Fetch Merge.kif (~80 MB)
make cache          # Generate sumo_hierarchy.json
make test
```

## Usage

```python
from sumo import SUMOTypeRegistry

registry = SUMOTypeRegistry(cache_path="data/sumo_hierarchy.json")

# Classify entities
registry.classify("person", "Dr. Jane Smith")  # -> "Human"
registry.classify("technology", "PostgreSQL database")  # -> "Database"

# Subsumption
registry.is_subclass("Automobile", "Vehicle")  # -> True

# Ontological distance
registry.get_ontological_distance("Automobile", "Aircraft")  # -> 2

# Query expansion
registry.get_descendants("Vehicle")  # -> ["Automobile", "Aircraft", "WaterVehicle", ...]
```

## Architecture

See [ADR-145](../cognitive-architecture-docs/adr/ADR-145-sumo-formal-ontology-layer.md) and the [architecture doc](../cognitive-architecture-docs/architecture/sumo-formal-ontology-layer.md).
