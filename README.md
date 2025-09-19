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

# 2) Activate Python env (create if missing)
conda activate ymb-py311 || conda create -n ymb-py311 python=3.11 -y && conda activate ymb-py311
python -V   # should show Python 3.11.x

# 3) Use Node 20
export NVM_DIR="$HOME/.nvm"; . "$NVM_DIR/nvm.sh"
nvm use 20 || nvm install 20 && nvm use 20
node -v

# 4) (Coming soon in Milestone 1.1)
# Backend/Frontend scaffolding, Makefile targets, and CI
```

## Repo Structure (current vs planned)
Current:
- `.cursor/rules/` – Cursor rules for structure, standards, CI
- `your_morning_brief_PRD.md` – Product requirements
- `MVP_imp_plan.md` – Milestone plan
- `M1.1_spec.md` – Repo/CI/dev scaffolding spec
- `environment.yml` – Conda env recipe (from history)

Planned (per MVP plan):
- `backend/` – FastAPI service with `/healthz`, `/readyz`, `/version`, RSS ingestion, ranking, summarization
- `frontend/` – Next.js app (Topic management, Daily Brief UI)
- `.github/workflows/` – CI for lint, type-check, tests

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

## License
TBD
