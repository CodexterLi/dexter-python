-include .env
export

.PHONY: install dev test lint format upgrade

install:
	uv sync

dev:
	uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

test:
	uv run pytest -v

lint:
	uvx ruff check .
	uvx ruff format --check .

format:
	uvx ruff check . --fix && uvx ruff format .

upgrade:
	uv lock --upgrade
	uv sync
