.PHONY: help setup test lint

help: ## Show this help
	@echo "High Availability The Hard Way"
	@echo ""
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

setup: ## Set up development environment
	python -m venv venv
	./venv/bin/pip install --upgrade pip
	./venv/bin/pip install -r docuask/api/requirements.txt
	./venv/bin/pip install -r docuask/worker/requirements.txt

test: ## Run all tests
	./venv/bin/pytest -v

lint: ## Run linting
	./venv/bin/black --check docuask/ labs/ shared/
	./venv/bin/ruff check docuask/ labs/ shared/