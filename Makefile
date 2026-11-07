# Works with GNU make on Windows (cmd) and Linux/macOS (sh): recipes are plain commands only.
# On Windows: winget install ezwinports.make ; uv via `python -m pip install --user uv`.
UV ?= python -m uv

SPEC ?= configs/experiments/rq2.yaml
WORKERS ?= 4

.PHONY: setup test smoke lint format sweep-dry sweep

sweep-dry:
	$(UV) run python scripts/sweep.py $(SPEC) --dry-run --workers $(WORKERS)

sweep:
	$(UV) run python scripts/sweep.py $(SPEC) --workers $(WORKERS)

setup:
	git submodule update --init
	$(UV) sync

test:
	$(UV) run pytest

smoke:
	$(UV) run python scripts/smoke.py

lint:
	$(UV) run ruff check src scripts tests
	$(UV) run ruff format --check src scripts tests

format:
	$(UV) run ruff format src scripts tests
	$(UV) run ruff check --fix src scripts tests
