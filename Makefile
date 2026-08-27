# Makefile: repeatable SynapDrive-AI validation and research commands.

PY ?= python

.PHONY: help install install-dev run run-signal dashboard benchmark stress evidence-test \
        test test-core lint typecheck quality record replay docker-build docker-build-dev \
        docker-run docker-dashboard docker-test

help:
	@echo ""
	@echo "Core:"
	@echo "  make install         Install runtime dependencies"
	@echo "  make install-dev     Install development dependencies"
	@echo "  make run             Run a governed text cycle"
	@echo "  make run-signal      Run an explicit synthetic fixture cycle"
	@echo "  make dashboard       Run the local WSGI dashboard"
	@echo "  make test            Run the complete pytest suite"
	@echo "  make test-core       Run the core test subset"
	@echo "  make quality         Compile + test + validation smoke"
	@echo "  make lint            Run ruff"
	@echo "  make typecheck       Run pyright"
	@echo ""
	@echo "Research tools:"
	@echo "  synapdrive-benchmark DATASET.npz"
	@echo "  synapdrive-stress --runs 100 --seed 7"
	@echo "  synapdrive-evidence verify-chain evidence.jsonl"
	@echo ""

install:
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -e .

install-dev:
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -e ".[dev]"

run:
	$(PY) -m synapdrive_ai --text "move left" --image road --no-delay

run-signal:
	$(PY) -m synapdrive_ai --signal walk --no-delay

dashboard:
	$(PY) -m synapdrive_ai.interface.web_dashboard

benchmark:
	@echo "Usage: synapdrive-benchmark DATASET.npz [--decoder ensemble]"

stress:
	$(PY) -m synapdrive_ai.stress.cli --runs 25 --seed 7

evidence-test:
	@echo "Usage: synapdrive-evidence verify-chain evidence.jsonl"

test:
	$(PY) -m pytest -q

test-core:
	$(PY) -m pytest -q synapdrive_ai/tests --ignore=synapdrive_ai/tests/test_web_dashboard.py

lint:
	$(PY) -m ruff check .

typecheck:
	$(PY) -m pyright

quality:
	$(PY) -m compileall -q synapdrive_ai core scripts
	$(PY) -m pytest -q
	$(PY) -m scripts.run_v1_validation

record:
	$(PY) -m synapdrive_ai --text "move left" --image road --record runs.jsonl --no-delay

replay:
	$(PY) -m synapdrive_ai --replay runs.jsonl

docker-build:
	docker build -t synapdrive-ai:latest .

docker-build-dev:
	docker build --build-arg INSTALL_DEV=true -t synapdrive-ai:dev .

docker-run: docker-build
	docker run --rm synapdrive-ai:latest python -m synapdrive_ai --text "move left" --no-delay

docker-dashboard: docker-build
	docker run --rm -p 5055:5055 synapdrive-ai:latest python -m synapdrive_ai.interface.web_dashboard

docker-test: docker-build-dev
	docker run --rm synapdrive-ai:dev pytest -q
