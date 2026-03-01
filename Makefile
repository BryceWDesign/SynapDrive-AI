# Makefile — fast, repeatable commands for SynapDrive-AI

PY ?= python

.PHONY: help install install-dev run run-signal dashboard test lint typecheck record replay \
        docker-build docker-build-dev docker-run docker-dashboard docker-test

help:
	@echo ""
	@echo "Targets:"
	@echo "  make install         Install runtime deps"
	@echo "  make install-dev     Install dev deps (ruff/pyright/pytest/pre-commit)"
	@echo "  make run             Run one CLI cycle (text example)"
	@echo "  make run-signal      Run one CLI cycle (signal example)"
	@echo "  make dashboard       Run the Flask dashboard (localhost:5055)"
	@echo "  make test            Run pytest"
	@echo "  make lint            Run ruff"
	@echo "  make typecheck       Run pyright"
	@echo "  make record          Record a run to runs.jsonl (no-delay)"
	@echo "  make replay          Replay runs.jsonl"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build     Build runtime image"
	@echo "  make docker-build-dev Build dev image (includes dev deps)"
	@echo "  make docker-run       Run CLI in container (text example)"
	@echo "  make docker-dashboard Run dashboard in container (localhost:5055)"
	@echo "  make docker-test      Run pytest in container"
	@echo ""

install:
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -r requirements.txt
	$(PY) -m pip install -e . || true

install-dev: install
	$(PY) -m pip install -r requirements-dev.txt

run:
	$(PY) -m synapdrive_ai --text "move left" --image road

run-signal:
	$(PY) -m synapdrive_ai --signal walk

dashboard:
	$(PY) -m synapdrive_ai.interface.web_dashboard

test:
	$(PY) -m pytest -q

lint:
	$(PY) -m ruff check .

typecheck:
	$(PY) -m pyright

record:
	$(PY) -m synapdrive_ai --text "move left" --image road --record runs.jsonl --no-delay

replay:
	$(PY) -m synapdrive_ai --replay runs.jsonl

# -----------------------
# Docker targets
# -----------------------

docker-build:
	docker build -t synapdrive-ai:latest .

docker-build-dev:
	docker build --build-arg INSTALL_DEV=true -t synapdrive-ai:dev .

docker-run: docker-build
	docker run --rm synapdrive-ai:latest python -m synapdrive_ai --text "move left" --image road

docker-dashboard: docker-build
	docker run --rm -p 5055:5055 synapdrive-ai:latest python -m synapdrive_ai.interface.web_dashboard

docker-test: docker-build-dev
	docker run --rm synapdrive-ai:dev pytest -q
