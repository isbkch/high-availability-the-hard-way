.PHONY: up down smoke-test reset logs test

COMPOSE := $(shell if docker compose version >/dev/null 2>&1; then echo "docker compose"; else echo "docker-compose"; fi)

up:
	./scripts/up.sh

down:
	$(COMPOSE) down

smoke-test:
	./scripts/smoke-test.sh

reset:
	./scripts/reset.sh

logs:
	./scripts/logs.sh

test:
	python3 -m pytest tests
