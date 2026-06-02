.PHONY: run worker migrate seed test lint

run:
	uvicorn app.main:app --reload --port 8000

worker:
	python -m worker.main

migrate:
	alembic upgrade head

seed:
	python scripts/seed_db.py

test:
	pytest

lint:
	ruff check .
