.DEFAULT_GOAL := help
.PHONY: help install dev test test-backend test-frontend lint format typecheck coverage migrate seed check

BACKEND  := backend
FRONTEND := frontend

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

install: ## Install backend (Poetry) and frontend (npm) dependencies
	cd $(BACKEND) && poetry install
	cd $(FRONTEND) && npm install

dev: ## Run backend (:8000) and frontend (:5173) dev servers
	cd $(BACKEND) && poetry run uvicorn pf_tracker.main:app --reload & \
	cd $(FRONTEND) && npm run dev

test: test-backend test-frontend ## Run all test suites

test-backend: ## Run backend tests
	cd $(BACKEND) && poetry run pytest

test-frontend: ## Run frontend tests
	cd $(FRONTEND) && npm run test

lint: ## Lint both stacks
	cd $(BACKEND) && poetry run ruff check .
	cd $(FRONTEND) && npm run lint

format: ## Auto-format both stacks
	cd $(BACKEND) && poetry run ruff format .
	cd $(FRONTEND) && npm run format

typecheck: ## Type-check both stacks
	cd $(BACKEND) && poetry run mypy
	cd $(FRONTEND) && npm run typecheck

coverage: ## Run tests with coverage thresholds enforced
	cd $(BACKEND) && poetry run pytest --cov=pf_tracker --cov-report=term-missing --cov-fail-under=85
	cd $(FRONTEND) && npm run coverage

migrate: ## Apply database migrations (available from phase 3)
	cd $(BACKEND) && poetry run alembic upgrade head

seed: ## Seed local data (available from phase 3)
	@echo "seed: not implemented until phase 3"

check: lint typecheck test ## Run the full CI gate locally
