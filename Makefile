.PHONY: install install-dev test lint format format-check typecheck ci clean download-kif cache build-wheel

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

test:
	pytest tests/ -v

lint:
	ruff check sumo/ tests/

format:
	ruff format sumo/ tests/

format-check:
	ruff format --check sumo/ tests/

typecheck:
	mypy sumo/

ci: lint format-check test

download-kif:
	@echo "Downloading SUMO Merge.kif from Ontology Portal..."
	mkdir -p data
	curl -L -o data/Merge.kif https://raw.githubusercontent.com/ontologyportal/sumo/master/Merge.kif
	@echo "Downloaded $$(wc -c < data/Merge.kif) bytes to data/Merge.kif"

cache: data/Merge.kif
	python -m sumo.build_cache --kif data/Merge.kif --output sumo/data/sumo_hierarchy_v1.json

build-wheel: download-kif cache
	python -m build

clean:
	rm -rf __pycache__ .pytest_cache .mypy_cache .ruff_cache *.egg-info dist build
	find . -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
