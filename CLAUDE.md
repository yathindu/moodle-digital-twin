# Project: Moodle Digital Twin

## What this is
A read-only, live-synced predictive digital twin of students in a Moodle course
(University of Peradeniya, internship project). Pulls Moodle activity data,
builds per-student engagement features, predicts at-risk AND high-potential
students (dual direction — most existing work only does at-risk), and exposes
results via a dashboard and an LLM query layer. A sandboxed closed-loop
intervention prototype demonstrates writing back to Moodle safely.

Currently developing against a local Moodle instance (Docker, moodlehq/moodle-docker)
since real university API access has not been granted yet.

## Stack
- Backend: FastAPI + SQLAlchemy, async routes
- DB: PostgreSQL (or SQLite for local dev)
- Moodle access: Web Services REST API only — no direct DB access unless explicitly told otherwise
- ML: XGBoost, scikit-learn
- Frontend: Streamlit
- LLM layer: Groq API
- Dev environment: WSL2 (Ubuntu) on Windows, Docker Desktop with WSL integration

## Conventions
- All Moodle API responses validated through Pydantic schemas before use — never pass raw JSON downstream
- Never assume a Moodle Web Service function exists from memory — verify against the actual enabled-function list on this instance before writing a client method for it
- No raw SQL outside a dedicated data-access layer (app/services or app/moodle)
- Time-respecting train/test splits only — never randomly shuffle time-series student data
- Write-back/messaging logic must live in an isolated `sandbox/` module, never in the main pipeline
- Any write-back code must refuse to run unless MOODLE_BASE_URL contains "localhost"
- Read credentials only from environment variables (.env, never committed)

## Known environment quirks
- Native `docker` inside this WSL shell can hit group-permission issues; a `.bin/docker` wrapper calling `docker.exe` may be present as fallback — prefer native if it works
- Project files must live under Linux home (`~/moodle-digital-twin`), not `/mnt/c/...`

## Current phase
Week 1–2 of a 12-week plan (started July 23, 2026). Local Moodle instance up,
Web Services enabled, admin token generated. Next: FastAPI scaffold, Moodle
API client, seed synthetic student data.

## Reporting/research context
Research gap: existing Moodle prediction systems stop at prediction, never close
the loop back into the live system, and rarely detect high-potential students
alongside at-risk. The dual-classifier design and sandboxed write-back module
are the actual research contribution — keep this framing when naming/structuring things.

## Working notes
Log significant design decisions to NOTES.md as they happen.
