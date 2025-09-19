## MVP Implementation Plan: Your Morning Brief

### Scope
- Aligns with PRD Phase 1 (Weeks 1-6): RSS aggregation, basic AI processing, multi-topic management, learning loop, and minimal frontend for daily use.
- Principle: Keep milestones small, independently testable, and demoable.

### Environments & Tooling
- Backend: Python, FastAPI
- Data: PostgreSQL, Redis
- AI: OpenAI (summarization), simple baseline relevance (keywords/TF-IDF)
- Frontend: Next.js + Tailwind CSS
- Infra: Docker (dev), simple scheduler (APScheduler or Celery beat)
- CI: GitHub Actions (lint, type-check, tests)

---

## Phase 1 (Weeks 1-2): RSS Aggregation + Basic AI Processing

### Milestone 1.1 – Repo, CI, and Dev Scaffolding
- Goal: Establish project structure and quality gates.
- Deliverables:
  - Monorepo or two folders `backend/`, `frontend/` with READMEs
  - GitHub Actions workflow: lint (ruff/eslint), type-check (mypy/tsc), tests
  - Dev containers / Dockerfiles and `make` targets (run, test, fmt)
- Acceptance:
  - CI runs automatically on PRs and `main`, all checks pass on a hello-world test.

Note: Detailed spec can be found in [M1.1_spec.md](M1.1_spec.md).

### Milestone 1.2 – FastAPI Skeleton + Health/Version Endpoints
- Goal: Running API baseline.
- Deliverables:
  - FastAPI app with `/healthz`, `/readyz`, `/version`
  - Structured logging and basic error middleware
- Acceptance:
  - `GET /healthz` returns 200 locally and in Docker.

### Milestone 1.3 – Database Bootstrap (PostgreSQL) + Migrations
- Goal: Persistent storage foundation.
- Deliverables:
  - Migration tooling (Alembic)
  - Initial schema: `users`, `topics`, `sources`, `articles`
- Acceptance:
  - `alembic upgrade head` succeeds; tables visible; rollback works.

### Milestone 1.4 – RSS Source Seeding and Single-Feed Ingestion
- Goal: Fetch and parse first feed.
- Deliverables:
  - Seed top-quality sources list (start with 3 feeds)
  - Ingestion module using `feedparser` for one feed
- Acceptance:
  - CLI command ingests ≥10 items from 1 feed and stores raw fields.

### Milestone 1.5 – Normalization, Storage, and Deduplication
- Goal: Store clean article records.
- Deliverables:
  - Normalization pipeline (title, summary, link, published_at)
  - Deduplication via stable content hash + DB unique index
- Acceptance:
  - Re-ingestion of same feed yields 0 duplicates; idempotent.

### Milestone 1.6 – Expand to 10+ Feeds and Basic Error Handling
- Goal: Broader coverage with robustness.
- Deliverables:
  - Ingest 10–15 sources; per-source backoff/retry
  - Source-level status metrics
- Acceptance:
  - ≥10 sources successfully ingest; failures logged without crash.

### Milestone 1.7 – Baseline Relevance (Keyword/TF-IDF) per Topic
- Goal: First-pass relevance scoring.
- Deliverables:
  - Topic model: name + keyword bag
  - Relevance score function (simple cosine/keyword match)
- Acceptance:
  - Given a topic with keywords, top 10 related articles are returned deterministically.

### Milestone 1.8 – Summarization Service (OpenAI)
- Goal: 2–3 sentence summaries.
- Deliverables:
  - Summarization module with retry and cost guardrails
  - Store summaries in `article_summaries` table with provenance
- Acceptance:
  - For 5 sample articles, summaries are generated under token limits.

---

## Phase 2 (Weeks 3-4): Multi-Topic Management + Learning Loop

### Milestone 2.1 – Topic CRUD and Association
- Goal: Users manage multiple topics.
- Deliverables:
  - API: create/list/update/delete topics; associate to `user_id`
  - Persist topic keywords
- Acceptance:
  - Postman collection runs CRUD flows; data persists.

### Milestone 2.2 – Daily Top-3 Selection per Topic
- Goal: Enforce “exactly 3 per topic daily”.
- Deliverables:
  - Ranker: recency + relevance + source credibility baseline
  - Persist daily picks in `deliveries` with freeze/immutability
- Acceptance:
  - For a topic, exactly 3 are stored for the day; repeats prevented.

### Milestone 2.3 – Feedback API (Thumbs Up/Down + Optional Text)
- Goal: Collect signals for learning.
- Deliverables:
  - Endpoint to rate a delivered article and optional comment
  - `feedback` table with timestamps
- Acceptance:
  - Ratings recorded; duplicate rating updates last value cleanly.

### Milestone 2.4 – Simple Learning Update
- Goal: Adapt topic keywords from feedback.
- Deliverables:
  - Nightly job adjusts keyword weights from positive/negative feedback
- Acceptance:
  - After synthetic feedback, subsequent rankings shift as expected.

### Milestone 2.5 – Scheduler/Worker for Polling and Jobs
- Goal: Automate ingestion and selection.
- Deliverables:
  - Scheduler (APScheduler or Celery beat)
  - Jobs: ingest every 5 min; summarize on save; daily selection at 6am local
- Acceptance:
  - Jobs run on schedule locally; logs confirm execution windows.

### Milestone 2.6 – Caching Layer (Redis) for Read APIs
- Goal: Fast user responses.
- Deliverables:
  - Cache recent topic results and daily picks
  - Cache busting on feedback or new selection
- Acceptance:
  - P95 < 200ms for cached `GET /topics/:id/daily` on dev data.

---

## Phase 3 (Weeks 5-6): Minimal Frontend for Daily Use

### Milestone 3.1 – Next.js App Skeleton + Design System Setup
- Goal: Frontend baseline.
- Deliverables:
  - Next.js app, Tailwind, basic layout, env wiring
- Acceptance:
  - App runs locally; `/healthz` backend status shown in footer.

### Milestone 3.2 – Topic Management UI
- Goal: Create/edit/delete topics.
- Deliverables:
  - Topic list + modal to add/edit keywords
- Acceptance:
  - Can add a topic and confirm via API that it exists.

### Milestone 3.3 – Daily Brief UI (Top 3 per Topic)
- Goal: Core daily view.
- Deliverables:
  - Topic sections with 3 article cards each
  - Each card: title (link), summary, source, published time
- Acceptance:
  - For seeded topics, 3 cards render with live data.

### Milestone 3.4 – Feedback Controls and Basic Persistence
- Goal: Close the loop.
- Deliverables:
  - Thumbs up/down per card; optional text feedback dialog
- Acceptance:
  - UI actions persist and are visible in backend logs/DB.

### Milestone 3.5 – Save/Share (MVP) and Empty States
- Goal: Essential usability polish.
- Deliverables:
  - Save to local list (DB), copy link share, empty/loading states
- Acceptance:
  - Saved items appear in a basic “Saved” view; share copies URL.

### Milestone 3.6 – E2E Smoke, Demo Script, and Metrics
- Goal: Validate end-to-end and demonstrate value.
- Deliverables:
  - Cypress/Playwright smoke covering topic add → brief → feedback
  - Basic metrics (request count, job success, summary token usage)
  - Demo script and sample topics for presentation
- Acceptance:
  - E2E passes locally and in CI; demo runs in < 10 minutes.

---

## APIs (Minimum for MVP)
- GET `/healthz`, `/readyz`, `/version`
- POST `/topics`, GET `/topics`, PATCH `/topics/:id`, DELETE `/topics/:id`
- GET `/topics/:id/daily` → 3 articles with summaries and attribution
- POST `/deliveries/:delivery_id/feedback` → {rating: up|down, text?: string}

---

## Data Model (Initial)
- `users(id, email)` – stub for MVP
- `topics(id, user_id, name, keywords, created_at)`
- `sources(id, name, url, credibility_score)`
- `articles(id, source_id, title, link, summary_raw, published_at, content_hash)`
- `article_summaries(article_id, summary_text, model, created_at)`
- `deliveries(id, user_id, topic_id, date, article_id)`
- `feedback(id, delivery_id, rating, comment, created_at)`

---

## Testing & Validation Strategy
- Unit: ingestion parsers, scoring, summarization wrapper
- Integration: DB migrations, dedup, ranker determinism, scheduler
- Contract: API schemas via OpenAPI, frontend client generation
- E2E: topic creation → brief view → feedback persists
- Performance: cached daily brief P95 < 200ms on dev data

---

## Risks & Mitigations (MVP)
- Feed reliability: diversify sources; per-source retries/backoff
- AI costs: summarize only candidate shortlist; cache summaries
- Duplicate/near-duplicate: robust hashing; title+link+date heuristics
- Time-to-delivery: prioritize scheduler and dedup before learning loop

---

## Milestone Checklist (for tracking)
- [ ] 1.1 Repo, CI
- [ ] 1.2 FastAPI skeleton
- [ ] 1.3 DB bootstrap
- [ ] 1.4 Single-feed ingestion
- [ ] 1.5 Normalization & dedup
- [ ] 1.6 10+ feeds & robustness
- [ ] 1.7 Baseline relevance
- [ ] 1.8 Summarization
- [ ] 2.1 Topic CRUD
- [ ] 2.2 Daily top-3 selection
- [ ] 2.3 Feedback API
- [ ] 2.4 Learning update
- [ ] 2.5 Scheduler/jobs
- [ ] 2.6 Caching
- [ ] 3.1 Next.js skeleton
- [ ] 3.2 Topic UI
- [ ] 3.3 Daily Brief UI
- [ ] 3.4 Feedback UI
- [ ] 3.5 Save/Share & states
- [ ] 3.6 E2E, demo, metrics
