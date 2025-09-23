# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Product Context

**Your Morning Brief** is an AI-powered news curation service that will:

- Curate exactly 3 high-quality articles per topic daily
- Support multiple topics with persistent learning context
- Use RSS feeds + AI for content filtering and summarization
- Learn from user feedback to improve relevance

**Current Status:** Milestone 1.5 (Normalization, Storage, and Deduplication) - Complete RSS ingestion pipeline with comprehensive normalization and deduplication capabilities. Includes content normalization, stable content hashing, idempotent storage, character encoding security, and comprehensive test coverage. Next milestones will expand to 10+ feeds (M1.6) and add AI processing capabilities (M1.7-M1.8).

**Key Documents:**

- `your_morning_brief_PRD.md`: Complete product requirements
- `MVP_imp_plan.md`: Detailed implementation roadmap with 18 milestones
- `M1.1_spec.md` through `M1.8_spec.md`: Milestone specifications with security enhancements

## Development Environment Setup

### Initial Setup

```bash
# One-time setup (install dependencies, pre-commit hooks)
make setup

# Verify conda environment is properly configured
conda run -n ymb-py311 python --version  # Should show Python 3.11.x
```

### Development Stack

```bash
# Start full stack (Postgres, Redis, backend, frontend)
make up

# Stop development stack
make down

# Run individual services
make backend    # FastAPI on :8000
make frontend   # Next.js on :3000
```

## Development Commands

### Quality Checks (All Commands)

```bash
# Format code
make fmt

# Lint all code (required before commits)
make lint

# Run all tests
make test

# Type check (prevents mypy failures)
make typecheck

# Check dependency sync (prevents CI failures)
make check-deps
```

### Backend-Specific Commands

**⚠️ MANDATORY: Use Conda Environment `ymb-py311` for All Backend Development**

```bash
# Testing
conda run -n ymb-py311 pytest                        # Run all tests
conda run -n ymb-py311 pytest tests/test_health.py   # Specific test file
conda run -n ymb-py311 pytest -k "test_healthcheck"  # Test pattern matching

# Type checking
conda run -n ymb-py311 mypy app/                      # Type checking (app only)

# Running the application
conda run -n ymb-py311 uvicorn app.main:app --reload

# Package management
conda run -n ymb-py311 pip install package-name
```

### Frontend-Specific Commands

```bash
cd frontend && npm test                      # Vitest tests
cd frontend && npx eslint .                  # Linting
cd frontend && npx tsc --noEmit             # Type checking
```

### Database Operations

```bash
make db-upgrade              # Apply latest migrations
make db-downgrade           # Rollback one migration
make db-reset               # Reset and reapply all migrations
make db-create-migration    # Create new migration (interactive)
make db-history             # View migration history
```

### RSS Ingestion Operations

```bash
# Seed initial RSS sources
make seed-sources

# Ingest from specific feed
make ingest-one FEED_URL="https://example.com/rss"
```

## Architecture Overview

### Project Structure

- **`backend/`**: FastAPI application (Python 3.11)
  - `app/main.py`: FastAPI app creation and configuration
  - `app/api/health.py`: Health check endpoints (`/healthz`, `/readyz`, `/version`)
  - `app/ingestion/`: RSS feed processing pipeline
  - `app/models/`: SQLAlchemy database models
  - Uses ruff, black, mypy for code quality

- **`frontend/`**: Next.js application (Node 20, TypeScript strict)
  - App router structure under `app/`
  - Tailwind CSS for styling
  - Vitest for testing, ESLint for linting

- **`docker-compose.dev.yml`**: Development stack with Postgres, Redis, backend, frontend

### Key Technical Details

- Backend runs on port 8000, frontend on port 3000
- Backend includes CORS middleware allowing localhost:3000
- Frontend fetches backend health status from `/healthz` endpoint
- Development environment uses Docker Compose with health checks
- Both apps are containerized with volume mounts for development

### Development Workflow

- Uses Conventional Commits (feat, fix, chore, docs, refactor, test, ci)
- Pre-commit hooks enforce code quality (ruff, black, mypy, eslint, prettier, dependency sync)
- CI pipeline runs on GitHub Actions with lint, type-check, and test jobs
- All quality gates must pass before merge

## Quality Standards

### Backend (Python 3.11 + FastAPI)

- **Python Environment**: Use Conda environment `ymb-py311` for all backend development
  - Do NOT use system pip or create additional virtual environments
  - Always use `conda run -n ymb-py311` prefix for backend commands
- **Type Safety**: Type hints required for all public functions and endpoints
- **API Design**: Use Pydantic models for API responses and input validation
- **Logging**: Structured logging with request IDs (mask sensitive data)
- **Configuration**: Environment-based configuration (never commit secrets)
- **Testing**: pytest with deterministic tests
- **Security**: All code must implement security controls from milestone specifications

### Frontend (Next.js + TypeScript)

- TypeScript strict mode required
- ESLint with zero warnings policy
- Accessible UI following WCAG basics
- Feature-based organization with reusable components

### Required CI Checks

- **Backend**: ruff, black, mypy, pytest, security tests
- **Frontend**: eslint, tsc --noEmit, unit tests
- **Security**: SAST scanning, dependency vulnerability checks
- **Performance**: Security overhead validation (<50ms per request)

## Dependency Management

### Critical Dual-File System

This project uses **two dependency files** that must be kept in sync:

1. **`backend/requirements.txt`**: Runtime dependencies for local development (Conda environment)
2. **`backend/pyproject.toml`**: Development dependencies used by GitHub Actions CI/CD

### Adding Dependencies

**For Runtime Dependencies:**

```bash
# 1. Add to requirements.txt
echo "new-package==1.2.3" >> backend/requirements.txt

# 2. Add to pyproject.toml dependencies section
# Edit backend/pyproject.toml and add: "new-package==1.2.3",

# 3. Verify sync
make check-deps

# 4. Install locally
conda run -n ymb-py311 pip install new-package==1.2.3
```

**For Development Dependencies:**

```bash
# Add only to pyproject.toml [project.optional-dependencies.dev]
# Then reinstall dev dependencies
conda run -n ymb-py311 pip install -e ./backend[dev]
```

### Automatic Validation

- **Pre-commit hooks** automatically run `make check-deps` before commits
- **Commits are blocked** if dependencies are out of sync
- **Clear error messages** show exactly what to fix

Example error output:

```bash
❌ Dependencies in requirements.txt but missing from pyproject.toml:
   - new-package
```

## Type Checking

### Environment Setup (One-Time)

```bash
# Install dev dependencies to match CI exactly
conda run -n ymb-py311 pip install -e ./backend[dev]
```

### Type Safety Requirements

**⚠️ MANDATORY: All Python code must pass mypy strict mode**

- **Pre-commit hooks** run `mypy app/` automatically before every commit
- **Commits are blocked** if type checking fails
- **GitHub Actions** runs the same mypy checks in CI

### Writing Type-Safe Code

**1. Always Add Type Hints to Functions**

```python
# ✅ Good: Complete type annotations
def process_articles(articles: list[Article], source_id: int) -> dict[str, int]:
    result: dict[str, int] = {"processed": 0, "errors": 0}
    return result

# ❌ Bad: Missing type annotations
def process_articles(articles, source_id):
    result = {"processed": 0, "errors": 0}
    return result
```

**2. Handle Optional Values Explicitly**

```python
# ✅ Good: Proper None handling
existing_source.credibility_score = validated_source.credibility_score or 0.5
existing_source.is_active = (
    validated_source.is_active if validated_source.is_active is not None else True
)

# ❌ Bad: Direct assignment of Optional to non-Optional
existing_source.credibility_score = validated_source.credibility_score  # May be None
```

**3. Use Explicit Type Annotations for Complex Returns**

```python
# ✅ Good: Explicit type annotation
cleaned: str = bleach.clean(content, tags=[], strip=True)
parsed_date: datetime = date_parser.parse(date_str)

# ❌ Bad: Relies on Any inference
cleaned = bleach.clean(content, tags=[], strip=True)  # Returns Any
```

### MyPy Configuration Understanding

The project uses `ignore_missing_imports = true` in `backend/pyproject.toml`:

```python
# ✅ WORKS WITHOUT type: ignore (due to ignore_missing_imports = true)
import feedparser
entries = feedparser.parse(url).entries

# ❌ UNNECESSARY: type: ignore comment
import feedparser  # type: ignore
entries = feedparser.parse(url).entries  # type: ignore

# ✅ STILL NEEDED: type: ignore for actual type issues
result: str = some_function_returning_any()  # type: ignore[assignment]
```

### Common MyPy Errors & Solutions

| Error                                          | Solution                                       |
| ---------------------------------------------- | ---------------------------------------------- |
| `Function is missing a return type annotation` | Add `-> ReturnType` or `-> None`               |
| `Incompatible types in assignment`             | Check Optional types, use proper None handling |
| `Call to untyped function`                     | Add type hints to function definition          |
| `Need type annotation for variable`            | Add explicit type: `var: Type = value`         |
| `Returning Any from function`                  | Add explicit type annotation for clarity       |

### Troubleshooting Type Issues

If mypy fails locally but passes in CI (or vice versa):

```bash
# 1. Verify environment consistency
conda run -n ymb-py311 which python
conda run -n ymb-py311 which mypy

# 2. Reinstall dependencies to match CI
conda run -n ymb-py311 pip install -e ./backend[dev]

# 3. Check for unnecessary type: ignore comments
grep -r "type: ignore" backend/app/
```

## Security Architecture

### Defense-in-Depth Security Model

**Layer 1: Network Security**

- **SSRF Protection**: Block private IP ranges (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, 127.0.0.0/8)
- **SSL/TLS Enforcement**: Always verify certificates, no self-signed certificates
- **Rate Limiting**: Per-source and per-endpoint rate limits
- **Request Validation**: Size limits, timeout enforcement, redirect limits

**Layer 2: Input Validation & Sanitization**

- **Pydantic Models**: Validate all inputs from external sources (RSS feeds, API requests)
- **HTML Sanitization**: Use `bleach` with empty allowlist to strip ALL HTML/JavaScript
- **Character Encoding**: Whitelist allowed encodings with confidence validation
- **URL Validation**: Only allow HTTP/HTTPS schemes, validate against blocklists

**Layer 3: Data Processing Security**

- **SQL Injection Prevention**: Mandatory use of SQLAlchemy ORM with parameterized queries
- **Content Hash Security**: Use sanitized inputs for stable hash generation
- **Unicode Normalization**: Apply NFKC normalization for consistent processing
- **Content Monitoring**: Track suspicious patterns and security events

**Layer 4: Application Security**

- **API Key Management**: Encrypt keys at rest using `cryptography.fernet`
- **Cost Controls**: Multi-layered budgets (requests, tokens, cost) with circuit breakers
- **Secure Error Handling**: Mask sensitive data in logs and error responses
- **Connection Security**: Proper pooling with SSL and timeout configuration

### Required Security Libraries

```txt
bleach==6.1.0              # HTML sanitization
cryptography==41.0.7       # API key encryption
slowapi==0.1.9             # Rate limiting
chardet==5.2.0             # Safe encoding detection
pydantic>=2.0.0           # Input validation
```

### Security Testing Requirements

All code must include security tests:

- XSS payload injection tests
- SQL injection attempt validation
- SSRF attack simulation
- Input validation bypass attempts
- API key security validation
- Rate limiting effectiveness tests

### Security Environment Variables

```bash
# API Security
OPENAI_API_KEY_ENCRYPTED=<encrypted_key>
API_KEY_ENCRYPTION_KEY_PATH=/app/secrets/encryption.key

# Rate Limiting
DAILY_REQUEST_LIMIT=1000
DAILY_TOKEN_BUDGET=50000
DAILY_COST_LIMIT_USD=10.0

# Network Security
SSL_VERIFY=true
MAX_RESPONSE_SIZE_MB=10
INGESTION_TIMEOUT_SEC=10

# Database Security
DATABASE_SSL_MODE=require
DATABASE_CONNECTION_TIMEOUT=30
```

## Milestone Management

### Milestone Completion Process

**MANDATORY: A milestone is NOT complete until ALL items below are checked off**

Use `make milestone-checklist` to see the full checklist. Always create a TodoWrite list with these exact items:

### Technical Implementation

- [ ] All technical requirements implemented and functional
- [ ] All acceptance criteria from milestone spec met
- [ ] Code quality checks pass: `make lint` (ruff, black, eslint)
- [ ] Type checking passes: `make typecheck` (mypy strict mode)
- [ ] All tests pass: `make test` (backend pytest, frontend vitest)
- [ ] Security requirements validated (if applicable)

### Documentation Updates (MANDATORY)

**⚠️ CRITICAL: Both MVP_imp_plan.md AND CLAUDE.md must be updated - do not skip either file!**

- [ ] Update `MVP_imp_plan.md` (REQUIRED):
  - [ ] Add ✅ checkmark to milestone title
  - [ ] Add "Status: **COMPLETED**" to milestone description
  - [ ] Add reference to detailed spec file (e.g., "Note: Detailed spec can be found in [M1.X_spec.md](M1.X_spec.md)")
  - [ ] Update milestone checklist at bottom of `MVP_imp_plan.md` from `[ ]` to `[x]`
- [ ] Update `CLAUDE.md` "Current Status" section to reflect latest completion

### Commit and Push

- [ ] Create comprehensive commit message describing implementation
- [ ] Push changes to GitHub
- [ ] Verify all changes are reflected in remote repository

### Process Validation

- [ ] All TodoWrite items marked as completed
- [ ] Documentation accurately reflects milestone completion
- [ ] Ready for next milestone or PR creation

**Personal Workflow Rule:** Never mark milestone TodoWrite items as "completed" without first completing ALL documentation updates above. BOTH MVP_imp_plan.md AND CLAUDE.md must be updated - no exceptions!

### Example Milestone Format

```markdown
### Milestone 1.3 – Database Bootstrap (PostgreSQL) + Migrations ✅

- Goal: Persistent storage foundation
- Status: **COMPLETED**
  Note: Detailed spec can be found in [M1.3_spec.md](M1.3_spec.md).
```

## Code Review Preferences

### Automated PR Reviews

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
   - SQL injection prevention via SQLAlchemy ORM with parameterized queries
   - XSS prevention via HTML sanitization with bleach library
   - SSRF protection blocking private IP ranges and enforcing SSL verification
   - API key encryption at rest using cryptography.fernet
   - Rate limiting and cost controls for external APIs
   - Input validation using Pydantic models for all external data
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

### Review Style

- Provide specific, actionable feedback with code examples
- Highlight both issues and good practices
- Suggest improvements rather than just pointing out problems
- Focus on education and knowledge sharing
- Be constructive and respectful

### Interacting with Claude in PRs

- Mention `@claude` in any PR comment to ask questions
- Use `/claude review` to trigger a full review
- Ask specific questions like `@claude is this SQL query optimized?`
- Request explanations: `@claude explain this architecture decision`

## Quick Reference

### Daily Development Workflow

```bash
# 1. Start development stack
make up

# 2. Make changes to code

# 3. Run quality checks before committing
make lint        # Required before commits
make typecheck   # Verify type safety
make test        # Ensure functionality

# 4. Commit (pre-commit hooks run automatically)
git add .
git commit -m "feat: implement new feature"

# 5. Push to GitHub
git push
```

### Environment Verification

```bash
# Verify conda environment setup
conda run -n ymb-py311 python --version
conda run -n ymb-py311 pip list | grep mypy

# Verify dependency sync
make check-deps

# Verify all quality gates pass
make lint && make typecheck && make test
```

### Troubleshooting Common Issues

**MyPy failures:**

- Ensure using conda environment: `conda run -n ymb-py311 mypy app/`
- Reinstall dev dependencies: `conda run -n ymb-py311 pip install -e ./backend[dev]`

**Dependency sync failures:**

- Run `make check-deps` to see what's missing
- Add missing packages to both files as needed

**Test failures:**

- Backend: `conda run -n ymb-py311 pytest -v`
- Frontend: `cd frontend && npm test`

**Docker issues:**

- Reset containers: `make down && make up`
- Check logs: `docker compose -f docker-compose.dev.yml logs`
