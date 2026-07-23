.PHONY: install run test lint format seed migrate docker-up docker-down

install:
	python -m pip install -e ".[dev]"

run:
	uvicorn app.main:app --reload

test:
	pytest --cov=app --cov-report=term-missing

lint:
	ruff check app tests scripts

format:
	ruff format app tests scripts
	ruff check --fix app tests scripts

seed:
	python scripts/seed.py

migrate:
	alembic upgrade head

docker-up:
	docker compose up --build

docker-down:
	docker compose down
