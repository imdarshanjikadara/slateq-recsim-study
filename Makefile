# Works with GNU make on Windows (cmd) and Linux/macOS (sh): recipes are plain commands only.
# On Windows: winget install ezwinports.make ; uv via `python -m pip install --user uv`.
UV ?= python -m uv

SPEC ?= configs/experiments/rq2.yaml
WORKERS ?= 4

.PHONY: setup test smoke lint format sweep-dry sweep analyze figures web reproduce-small reproduce-full

# results tables (results/rq2, results/rq3) -> figures (results/figures) -> site data (web/data)
analyze:
	$(UV) run python scripts/analyze.py

figures:
	$(UV) run python scripts/figures.py

web:
	$(UV) run python scripts/build_web.py

# fresh clone -> tiny end-to-end run (1 cell, 4 agents, 2 seeds, short training) -> tables, figures
reproduce-small: setup
	$(UV) run python scripts/sweep.py configs/experiments/small.yaml --workers $(WORKERS) --allow-dirty
	$(UV) run python scripts/analyze.py --spec configs/experiments/small.yaml --no-rq3 --out results/small
	$(UV) run python scripts/figures.py --rq2 results/small --rq3 results/small/none --out results/small/figures

# the full study (see README for measured wall-clock); resumable, run from a clean commit
reproduce-full:
	$(UV) run python scripts/sweep.py configs/experiments/rq2.yaml --workers $(WORKERS)
	$(UV) run python scripts/sweep.py configs/experiments/rq3.yaml --workers $(WORKERS)
	$(UV) run python scripts/analyze.py
	$(UV) run python scripts/figures.py
	$(UV) run python scripts/build_web.py

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
