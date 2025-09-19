# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

**Setup and Development:**

```bash
# Initial setup (install dependencies, pre-commit hooks)
make setup

# Start full development stack (Postgres, Redis, backend, frontend)
make up

# Stop development stack
make down

# Run individual services
make backend    # FastAPI on :8000
make frontend   # Next.js on :3000
```

**Quality Checks:**

```bash
# Format code
make fmt

# Lint all code (required before commits)
make lint

# Run all tests
make test

# Backend-specific commands
cd backend && pytest tests/test_health.py    # Single test file
cd backend && pytest -k "test_healthcheck"  # Specific test
cd backend && mypy app/                      # Type checking

# Frontend-specific commands
cd frontend && npm test                      # Vitest tests
cd frontend && npx eslint .                  # Linting
cd frontend && npx tsc --noEmit             # Type checking
```

## Architecture Overview

**Project Structure:**

- `backend/`: FastAPI application (Python 3.11)
  - `app/main.py`: FastAPI app creation and configuration
  - `app/api/health.py`: Health check endpoints (`/healthz`, `/readyz`, `/version`)
  - Uses ruff, black, mypy for code quality
- `frontend/`: Next.js application (Node 20, TypeScript strict)
  - App router structure under `app/`
  - Tailwind CSS for styling
  - Vitest for testing, ESLint for linting
- `docker-compose.dev.yml`: Development stack with Postgres, Redis, backend, frontend

**Key Technical Details:**

- Backend runs on port 8000, frontend on port 3000
- Backend includes CORS middleware allowing localhost:3000
- Frontend fetches backend health status from `/healthz` endpoint
- Development environment uses Docker Compose with health checks
- Both apps are containerized with volume mounts for development

**Development Workflow:**

- Uses Conventional Commits (feat, fix, chore, docs, refactor, test, ci)
- Pre-commit hooks enforce code quality (ruff, black, eslint, prettier)
- CI pipeline runs on GitHub Actions with lint, type-check, and test jobs
- All quality gates must pass before merge

## Product Context

This is **Your Morning Brief** - an AI-powered news curation service that will:

- Curate exactly 3 high-quality articles per topic daily
- Support multiple topics with persistent learning context
- Use RSS feeds + AI for content filtering and summarization
- Learn from user feedback to improve relevance

**Current Status:** Milestone 1.1 (Repo/CI/Dev Scaffolding) - basic infrastructure is complete. Next milestones will add RSS ingestion, AI processing, and topic management features.

**Key Documents:**

- `your_morning_brief_PRD.md`: Complete product requirements
- `MVP_imp_plan.md`: Detailed implementation roadmap with 18 milestones
- `M1.1_spec.md`: Current milestone specification

## Quality Standards

**Backend (Python 3.11 + FastAPI):**

- Type hints required for all public functions and endpoints
- Use Pydantic models for API responses
- Structured logging with request IDs
- Environment-based configuration (never commit secrets)
- pytest for testing with deterministic tests

**Frontend (Next.js + TypeScript):**

- TypeScript strict mode required
- ESLint with zero warnings policy
- Accessible UI following WCAG basics
- Feature-based organization with reusable components

**Required CI Checks:**

- Backend: ruff, black, mypy, pytest
- Frontend: eslint, tsc --noEmit, unit tests
