.PHONY: up down smoke-test break load-test apply-fix reset logs test

DOCKER_COMPOSE := $(shell if docker compose version >/dev/null 2>&1; then echo "docker compose"; else echo "docker-compose"; fi)
COMPOSE := $(DOCKER_COMPOSE) -f docker-compose.yml

up:
	./scripts/up.sh

down:
	$(COMPOSE) down

smoke-test:
	./scripts/smoke-test.sh

break:
	./scripts/break.sh

load-test:
	./scripts/load-test.sh

apply-fix:
	./scripts/apply-fix.sh

reset:
	./scripts/reset.sh

logs:
	./scripts/logs.sh

test:
	python3 -m pytest tests
