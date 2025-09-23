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

**Current Status:** Milestone 1.3 (Database Bootstrap) - PostgreSQL database layer with SQLAlchemy models and Alembic migrations is complete. Next milestones will add RSS ingestion, AI processing, and topic management features.

**Key Documents:**

- `your_morning_brief_PRD.md`: Complete product requirements
- `MVP_imp_plan.md`: Detailed implementation roadmap with 18 milestones
- `M1.1_spec.md`, `M1.2_spec.md`, `M1.3_spec.md`: Milestone specifications

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

## Code Review Preferences

**Automated PR Reviews:**

Claude will automatically review all non-draft pull requests focusing on:

1. **Code Quality & Best Practices**
   - Adherence to project conventions and patterns
   - DRY principle and code reusability
   - Clear naming and code organization
   - Proper error handling and edge cases

2. **Type Safety & Testing**
   - Type hints/annotations coverage
   - Test coverage for new functionality
   - Validation of input/output contracts
   - Error boundary implementation

3. **Security & Performance**
   - No hardcoded secrets or sensitive data
   - SQL injection and XSS prevention
   - Efficient algorithms and database queries
   - Proper resource cleanup

4. **Architecture Compliance**
   - Follow established project structure
   - Use existing utilities and patterns
   - Maintain separation of concerns
   - API contract consistency

5. **Documentation & Maintainability**
   - Clear function/class documentation for public APIs
   - Complex logic explained with inline comments
   - Updated tests for changed behavior
   - Meaningful commit messages

**Review Style:**

- Provide specific, actionable feedback with code examples
- Highlight both issues and good practices
- Suggest improvements rather than just pointing out problems
- Focus on education and knowledge sharing
- Be constructive and respectful

**How to interact with Claude in PRs:**

- Mention `@claude` in any PR comment to ask questions
- Use `/claude review` to trigger a full review
- Ask specific questions like `@claude is this SQL query optimized?`
- Request explanations: `@claude explain this architecture decision`

## Milestone Progress Tracking

**IMPORTANT:** Always maintain accurate milestone status in `MVP_imp_plan.md`:

**When completing milestones:**

1. Update the milestone title with ✅ checkmark
2. Add "Status: **COMPLETED**" to the milestone description
3. Update the checklist at the bottom from `[ ]` to `[x]`
4. Reference the detailed spec file (e.g., `M1.3_spec.md`)
5. Update the "Current Status" section in this CLAUDE.md file

**When working on milestones:**

- Document any partial progress or blockers
- Update status descriptions to reflect current state
- Note any deviations from original specifications

**Example format:**

```markdown
### Milestone 1.3 – Database Bootstrap (PostgreSQL) + Migrations ✅

- Goal: Persistent storage foundation
- Status: **COMPLETED**
  Note: Detailed spec can be found in [M1.3_spec.md](M1.3_spec.md).
```

This ensures the team always has an accurate view of project progress and implementation status.
