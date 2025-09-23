.PHONY: setup fmt lint test up down backend frontend milestone-checklist check-deps typecheck

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
	@cd frontend && (npx eslint . --max-warnings=0)

typecheck:
	@echo "Type checking..."
	@cd backend && conda run -n ymb-py311 mypy app/

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

# RSS Ingestion operations
.PHONY: seed-sources ingest-one ingest-one-normalized

seed-sources:
	@echo "Seeding sources from JSON..."
	@cd backend && conda run -n ymb-py311 python -m app.ingestion.ingest_one --seed-sources app/data/sources.seed.json

ingest-one:
	@echo "Ingesting single feed..."
	@if [ -z "$(FEED_URL)" ]; then echo "Provide FEED_URL=..."; exit 1; fi
	@cd backend && conda run -n ymb-py311 python -m app.ingestion.ingest_one --feed-url "$(FEED_URL)"

ingest-one-normalized:
	@echo "Ingesting with normalization..."
	@if [ -z "$(FEED_URL)" ]; then echo "Provide FEED_URL=..."; exit 1; fi
	@cd backend && conda run -n ymb-py311 python -m app.ingestion.ingest_one --feed-url "$(FEED_URL)" --normalize

# Milestone completion process enforcement
milestone-checklist:
	@echo "🚨 MILESTONE COMPLETION CHECKLIST 🚨"
	@echo ""
	@echo "Before marking any milestone as COMPLETED, verify:"
	@echo ""
	@echo "✅ Technical Implementation:"
	@echo "   - All requirements implemented and functional"
	@echo "   - All acceptance criteria met"
	@echo "   - Code quality: make lint (passes)"
	@echo "   - Type checking: make typecheck (passes)"
	@echo "   - All tests: make test (passes)"
	@echo ""
	@echo "✅ Documentation Updates (MANDATORY):"
	@echo "   - MVP_imp_plan.md: Add ✅ to milestone title"
	@echo "   - MVP_imp_plan.md: Add 'Status: **COMPLETED**'"
	@echo "   - MVP_imp_plan.md: Add spec file reference"
	@echo "   - MVP_imp_plan.md: Update checklist [ ] to [x]"
	@echo "   - CLAUDE.md: Update 'Current Status' section"
	@echo ""
	@echo "✅ Commit and Push:"
	@echo "   - Comprehensive commit message"
	@echo "   - Push to GitHub"
	@echo ""
	@echo "📋 TodoWrite Rule: Include ALL above items in milestone todos"
	@echo ""
	@echo "See CLAUDE.md 'MANDATORY Milestone Completion Checklist' for details"

# Dependency management
check-deps:
	@echo "🔍 Checking dependency sync between requirements.txt and pyproject.toml..."
	@python3 scripts/check_dependency_sync.py
