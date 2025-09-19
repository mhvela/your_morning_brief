# Your Morning Brief

A personalized news agent that curates exactly 3 high‑quality articles per topic, daily.

## Project Docs

- Product Requirements: [your_morning_brief_PRD.md](./your_morning_brief_PRD.md)
- MVP Implementation Plan: [MVP_imp_plan.md](./MVP_imp_plan.md)
- Milestone 1.1 Detailed Spec: [M1.1_spec.md](./M1.1_spec.md)

## Prerequisites (your setup)

- Python via Miniforge/Conda (installed)
- Project env: `ymb-py311` (Python 3.11)
- Node via nvm (Node 20)

## Quickstart

```bash
# 1) Enter the project folder
cd "/Users/Mike/AI Coding Projects/your_morning_brief"

# 2) Ensure Node 20
export NVM_DIR="$HOME/.nvm"; . "$NVM_DIR/nvm.sh"; nvm use 20 || nvm install 20 && nvm use 20

# 3) Setup repo (dev tools, frontend deps, pre-commit)
make setup

# 4) Lint and type-check
make lint

# 5) Run tests
make test

# 6) Start dev stack (Postgres, Redis, backend, frontend)
make up

# 7) Visit frontend
open http://localhost:3000

# 8) Check backend health
curl http://localhost:8000/healthz
```

## Repo Structure (current vs planned)

Current:

- `.cursor/rules/` – Cursor rules for structure, standards, CI
- `your_morning_brief_PRD.md` – Product requirements
- `MVP_imp_plan.md` – Milestone plan
- `M1.1_spec.md` – Repo/CI/dev scaffolding spec
- `environment.yml` – Conda env recipe (from history)

Repo (Milestone 1.1):

- `backend/` – FastAPI app with `/healthz`, `/readyz`, `/version`; tests and tooling
- `frontend/` – Next.js app router; health indicator from backend; ESLint/TS/vitest
- `.github/workflows/ci.yml` – CI for lint, types, and tests
- `docker-compose.dev.yml` – Postgres, Redis, backend, frontend

## Why Python 3.11?

3.11 has the broadest library/tooling support and aligns with common CI baselines. We can add a CI matrix (3.11/3.12/3.13) and raise the floor later when everything is green.

## Environment Tips

- Recreate env: `conda env create -f environment.yml`
- Save minimal recipe: `conda env export --from-history > environment.yml`
- Keep Node pinned per project: add `.nvmrc` with `20` and run `nvm use`

## Contributing

- Conventional Commits (feat, fix, chore, docs, refactor, test, ci)
- Keep edits small and scoped per milestone

## Next Steps

- Implement Milestone 1.1 scaffolding per [M1.1_spec.md](./M1.1_spec.md)
- Add CI and initial `backend/` health endpoints

## Validation (Milestone 1.1)

- Fresh clone: `make setup && make lint && make test` all pass locally
- `make up` starts services; `curl http://localhost:8000/healthz` → 200 and `{status:"ok"}`
- Frontend shows backend health as "ok"
- CI green on PRs touching both apps

## License

MIT — see `LICENSE`
