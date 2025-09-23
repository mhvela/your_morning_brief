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

# Backend-specific commands (use Conda environment ymb-py311)
conda run -n ymb-py311 pytest                        # Run all tests
conda run -n ymb-py311 pytest tests/test_health.py   # Specific test file
conda run -n ymb-py311 pytest -k "test_healthcheck"  # Test pattern matching
conda run -n ymb-py311 mypy app/                      # Type checking

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

**Current Status:** Milestone 1.4 (RSS Source Seeding and Single-Feed Ingestion) - Complete RSS ingestion pipeline with comprehensive security architecture is implemented. Includes feed client with SSRF protection, XSS sanitization, content mapper, CLI tools, and full test suite. Next milestones will add normalization/deduplication (M1.5), expand to 10+ feeds (M1.6), and add AI processing capabilities (M1.7-M1.8).

**Key Documents:**

- `your_morning_brief_PRD.md`: Complete product requirements
- `MVP_imp_plan.md`: Detailed implementation roadmap with 18 milestones
- `M1.1_spec.md`, `M1.2_spec.md`, `M1.3_spec.md`: Milestone specifications
- `M1.4_spec.md`, `M1.5_spec.md`, `M1.6_spec.md`, `M1.7_spec.md`, `M1.8_spec.md`: Security-enhanced milestone specifications

## Quality Standards

**Backend (Python 3.11 + FastAPI):**

- **Python Environment**: Use Conda environment `ymb-py311` for all backend development
  - Installation: `conda run -n ymb-py311 python -m pip install ...`
  - Testing: `conda run -n ymb-py311 pytest`
  - Type checking: `conda run -n ymb-py311 mypy`
  - Running app: `conda run -n ymb-py311 uvicorn app.main:app --reload`
  - Do NOT use system pip or create additional venvs
- Type hints required for all public functions and endpoints
- Use Pydantic models for API responses and input validation
- Structured logging with request IDs (mask sensitive data)
- Environment-based configuration (never commit secrets)
- pytest for testing with deterministic tests
- **Security-first development**: All code must implement security controls from milestone specifications

**Frontend (Next.js + TypeScript):**

- TypeScript strict mode required
- ESLint with zero warnings policy
- Accessible UI following WCAG basics
- Feature-based organization with reusable components

**Required CI Checks:**

- Backend: ruff, black, mypy, pytest, security tests
- Frontend: eslint, tsc --noEmit, unit tests
- Security: SAST scanning, dependency vulnerability checks
- Performance: Security overhead validation (<50ms per request)

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

## Security Architecture

**Security-First Development Approach:**

The Your Morning Brief project implements a comprehensive defense-in-depth security model across all milestones:

### Layer 1: Network Security

- **SSRF Protection**: Block private IP ranges (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, 127.0.0.0/8)
- **SSL/TLS Enforcement**: Always verify certificates, no self-signed certificates
- **Rate Limiting**: Per-source and per-endpoint rate limits
- **Request Validation**: Size limits, timeout enforcement, redirect limits

### Layer 2: Input Validation & Sanitization

- **Pydantic Models**: Validate all inputs from external sources (RSS feeds, API requests)
- **HTML Sanitization**: Use `bleach` with empty allowlist to strip ALL HTML/JavaScript
- **Character Encoding**: Whitelist allowed encodings with confidence validation
- **URL Validation**: Only allow HTTP/HTTPS schemes, validate against blocklists

### Layer 3: Data Processing Security

- **SQL Injection Prevention**: Mandatory use of SQLAlchemy ORM with parameterized queries
- **Content Hash Security**: Use sanitized inputs for stable hash generation
- **Unicode Normalization**: Apply NFKC normalization for consistent processing
- **Content Monitoring**: Track suspicious patterns and security events

### Layer 4: Application Security

- **API Key Management**: Encrypt keys at rest using `cryptography.fernet`
- **Cost Controls**: Multi-layered budgets (requests, tokens, cost) with circuit breakers
- **Secure Error Handling**: Mask sensitive data in logs and error responses
- **Connection Security**: Proper pooling with SSL and timeout configuration

### Security Dependencies

**Required Security Libraries:**

```txt
bleach==6.1.0              # HTML sanitization
cryptography==41.0.7       # API key encryption
slowapi==0.1.9             # Rate limiting
chardet==5.2.0             # Safe encoding detection
pydantic>=2.0.0           # Input validation
```

### Security Testing Requirements

**All code must include security tests:**

- XSS payload injection tests
- SQL injection attempt validation
- SSRF attack simulation
- Input validation bypass attempts
- API key security validation
- Rate limiting effectiveness tests

### Security Configuration

**Environment Variables (All Required):**

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

### Security Monitoring

**Required Security Logging:**

- All failed authentication attempts
- Rate limit violations
- SSRF attempt blocks
- XSS sanitization events
- API cost overruns
- Unusual error patterns

**Log Security:**

- Never log API keys, passwords, or sensitive content
- Truncate content logs to 200 characters maximum
- Use structured logging with security event classification
- Implement log rotation and secure storage

### Compliance Standards

**Security Standards Alignment:**

- OWASP Top 10 compliance for web applications
- OWASP API Security Top 10 for API endpoints
- Data protection considerations for RSS content processing
- Secure coding practices per SANS/CWE guidelines

**Security Review Process:**

- Security review required for all milestone implementations
- Automated security scanning in CI/CD pipeline
- Manual security testing before production deployment
- Regular security audits and penetration testing
- Always plan implementation of feature specs with a TDD approach.
