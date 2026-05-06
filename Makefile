.PHONY: up down restart logs migrate test build shell

up:
	docker compose up -d

down:
	docker compose down

restart:
	docker compose restart api worker

build:
	docker compose build --no-cache

logs:
	docker compose logs -f api worker

migrate:
	docker compose exec api alembic upgrade head

test:
	pytest app/tests/ -v

shell:
	docker compose exec api bash
