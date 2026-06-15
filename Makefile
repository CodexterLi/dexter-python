-include .env
export

.PHONY: install dev worker docker-build docker-run-api docker-run-worker test lint format upgrade

install:
	uv sync

dev:
	uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

worker:
	uv run python -m app.worker

docker-build:
	docker build -t drexor-python:latest .

test:
	uv run pytest -v

lint:
	uvx ruff check .
	uvx ruff format --check .

format:
	uvx ruff check . --fix && uvx ruff format .

upgrade:
	uv lock --upgrade
	uv run python scripts/sync_pyproject_versions.py
	uv lock
	uv sync
