.DEFAULT_GOAL := help
.PHONY: help install dev test test-backend test-frontend lint format format-check typecheck coverage migrate seed check gen-api

BACKEND  := backend
FRONTEND := frontend

# Every frontend target shells out to npm, and npm is routinely installed outside
# the PATH a non-login shell inherits — so find it once and export it to every
# recipe, rather than making `make check` fail on a machine that has Node.
# Empty when nothing was found: appending unconditionally would put a bare ""
# on PATH, which means the current directory.
NODE_BIN := $(shell ./scripts/node-bin.sh 2>/dev/null)
ifneq ($(NODE_BIN),)
export PATH := $(NODE_BIN):$(PATH)
endif

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

format-check: ## Verify formatting without writing (same gate as CI)
	cd $(BACKEND) && poetry run ruff format --check .
	cd $(FRONTEND) && npm run format:check

typecheck: ## Type-check both stacks
	cd $(BACKEND) && poetry run mypy
	cd $(FRONTEND) && npm run typecheck

coverage: ## Run tests with coverage thresholds enforced (domain >= 95%, overall >= 85%)
	cd $(BACKEND) && poetry run pytest --cov=pf_tracker --cov-report=term-missing --cov-fail-under=85
	cd $(BACKEND) && poetry run coverage report --include="*/pf_tracker/domain/*" --fail-under=95
	cd $(FRONTEND) && npm run coverage

migrate: ## Apply database migrations (available from phase 3)
	cd $(BACKEND) && poetry run alembic upgrade head

seed: ## Seed local data (available from phase 3)
	@echo "seed: not implemented until phase 3"

gen-api: ## Regenerate the frontend API types from the backend OpenAPI schema
	cd $(BACKEND) && poetry run python -c "import json; from pf_tracker.main import create_app; print(json.dumps(create_app().openapi()))" > openapi.json
	cd $(FRONTEND) && npm run gen:api

check: lint format-check typecheck coverage ## Run the full CI gate locally (mirrors .github/workflows/ci.yml)
