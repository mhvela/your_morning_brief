# General Development Rules

## Project Overview

This is **Your Morning Brief** - an AI-powered news curation service that curates exactly 3 high-quality articles per topic daily using RSS feeds + AI for content filtering and summarization.

**Current Status:** Milestone 1.4 (RSS Source Seeding and Single-Feed Ingestion) completed. Complete RSS ingestion pipeline with comprehensive security architecture is implemented.

## Development Environment

### Mandatory Environment Requirements

- **Backend**: MUST use Conda environment `ymb-py311` for ALL backend development
- **Frontend**: Node 20 with TypeScript strict mode
- **Database**: PostgreSQL with SSL mode required
- **Cache**: Redis for session management

### Critical Commands

```bash
# Initial setup (one-time)
make setup

# Development stack
make up      # Start full stack (Postgres, Redis, backend, frontend)
make down    # Stop development stack

# Individual services
make backend    # FastAPI on :8000
make frontend   # Next.js on :3000
```

### Environment Verification

```bash
# Verify conda environment
conda run -n ymb-py311 python --version  # Should show Python 3.11.x

# Verify dependency sync
make check-deps

# Verify all quality gates pass
make lint && make typecheck && make test
```

## Architecture Constraints

### Backend (FastAPI + Python 3.11)

- **Environment**: Always use `conda run -n ymb-py311` prefix
- **Type Safety**: Type hints required for ALL public functions
- **API Design**: Pydantic models for ALL API responses and input validation
- **Database**: SQLAlchemy ORM with parameterized queries (security requirement)
- **Testing**: pytest with deterministic tests
- **Security**: All code MUST implement security controls from milestone specifications

### Frontend (Next.js + TypeScript)

- **TypeScript**: Strict mode required, zero type errors
- **Linting**: ESLint with zero warnings policy
- **Accessibility**: WCAG basics compliance
- **Organization**: Feature-based organization with reusable components

### Development Workflow Requirements

- **Commits**: Conventional Commits (feat, fix, chore, docs, refactor, test, ci)
- **Pre-commit**: Hooks enforce code quality automatically
- **CI Pipeline**: All quality gates must pass (lint, type-check, test, security)
- **Pull Requests**: Automatic Claude reviews for non-draft PRs

## Key Patterns

### Always Prefer

- Editing existing files over creating new ones
- Using existing utilities and patterns
- Following established project structure
- SQLAlchemy ORM over raw SQL
- Pydantic models for validation
- Structured logging with request IDs

### Never Do

- Create files unnecessarily
- Use system pip (use conda environment)
- Commit secrets or sensitive data
- Skip type annotations
- Bypass security controls
- Direct SQL queries (use ORM)

## Quality Gates

All development must pass these checks before commit:

```bash
make lint        # ruff, black, eslint
make typecheck   # mypy strict mode
make test        # pytest, vitest
make check-deps  # dependency sync validation
```

Pre-commit hooks automatically enforce these standards.
