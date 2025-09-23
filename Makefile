.PHONY: setup fmt lint test up down backend frontend

PYTHON := python3.11
PIP := pip
PKG_MANAGER := pnpm

setup:
	@echo "Setting up dev environment..."
	@$(PIP) install --upgrade pip
	@$(PIP) install pre-commit
	@pre-commit install
	@$(PIP) install -e backend[dev]
	@cd frontend && ($(PKG_MANAGER) install || npm install) || true

fmt:
	@echo "Formatting..."
	@ruff check --fix backend || true
	@black backend || true
	@cd frontend && (npx prettier -w "**/*.{ts,tsx,js,jsx,json,css,md}")

lint:
	@echo "Linting..."
	@ruff check backend
	@black --check backend
	@mypy backend
	@cd frontend && (npx eslint . --max-warnings=0)

test:
	@echo "Running tests..."
	@cd backend && pytest -q
	@cd frontend && (npm test --silent || $(PKG_MANAGER) test --silent)

up:
	@docker compose -f docker-compose.dev.yml up -d

down:
	@docker compose -f docker-compose.dev.yml down -v --remove-orphans

backend:
	@cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

frontend:
	@cd frontend && (next dev -p 3000 || npm run dev || $(PKG_MANAGER) dev)

# Database operations
.PHONY: db-upgrade db-downgrade db-reset db-create-migration db-history

db-upgrade:
	@echo "Upgrading database to latest migration..."
	@cd backend && alembic upgrade head

db-downgrade:
	@echo "Downgrading database by one migration..."
	@cd backend && alembic downgrade -1

db-reset:
	@echo "Resetting database..."
	@cd backend && alembic downgrade base && alembic upgrade head

db-create-migration:
	@echo "Creating new migration..."
	@read -p "Enter migration message: " msg; \
	cd backend && alembic revision --autogenerate -m "$$msg"

db-history:
	@echo "Migration history:"
	@cd backend && alembic history --verbose
