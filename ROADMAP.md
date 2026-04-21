# HF-SaaS — Deployment Roadmap

**Target subdomain**: `saas.ahmethamdiozen.site`
**Deploy order in pipeline**: 4th
**Scope**: only `hf-saas-backend/` + `hf-saas-frontend/`. The `saas_backend/` directory is a duplicate created for a Hugging Face Spaces push — **ignore it** for the VPS deploy.

**Status**: Python/FastAPI SaaS framework with background jobs (RQ), SQLAlchemy + Alembic, JWT, distributed locking, structured logging. Currently deployed on HF Spaces as "Rag Document Manager". Portable to own VPS for full control + branding.

---

## North Star

The **Python** showcase of the portfolio — proves polyglot depth beyond TypeScript/Node. A recruiter lands on `saas.ahmethamdiozen.site`, signs up, uploads a PDF, triggers a background ingestion job, watches progress update via the job API, then queries the document in a RAG chat. Admin sees the job queue, can cancel jobs. The point: FastAPI + RQ worker + SQLAlchemy + Alembic migrations + JWT + distributed locks + DDD module structure — a clean production-grade Python service, not a tutorial FastAPI app.

---

## Phase 0 — Deploy Blockers

### Code hygiene

- [ ] **Delete or gitignore `saas_backend/` in the working directory** to avoid confusion during future contributions. Keep only `hf-saas-backend/` and `hf-saas-frontend/` active.
- [ ] **Audit for HF Spaces-specific code** — anything referencing HF environment (SDK metadata in README frontmatter, `Dockerfile_HF`, `start_HF.sh`) shouldn't exist in the non-HF deploy. Remove or wrap in conditionals.

### Production config

- [ ] **Env validation at startup** — Pydantic Settings (`app/core/config.py`) should raise if `DATABASE_URL`, `SECRET_KEY`, `REDIS_URL`, `BACKEND_CORS_ORIGINS` are missing. No defaults for secrets.
- [ ] **CORS allowlist** — `BACKEND_CORS_ORIGINS=https://saas.ahmethamdiozen.site,https://ahmethamdiozen.site`.
- [ ] **Move OpenAI / LLM keys to env** — if the RAG layer uses OpenAI/Claude, verify no hardcoded keys in code.
- [ ] **Password policy** — minimum 8 chars, complexity rule. Today probably open.
- [ ] **JWT secret rotation plan** — SECRET_KEY for access + separate key for refresh; refresh token revocation table (already listed in features — verify).

### Deploy wiring

- [ ] **Write `docker-compose.prod.yaml`** with services: `api` (uvicorn), `worker` (RQ worker), Postgres (Coolify resource), Redis (Coolify resource), `frontend` (static).
- [ ] **Verify `Dockerfile` is VPS-ready** — not the `Dockerfile_HF` which is HF Spaces-specific. Multi-stage, non-root, `alembic upgrade head` before `uvicorn`.
- [ ] **RQ worker as separate Coolify service** — one API container, one or more worker containers sharing the same Redis. Don't run worker inside API process.
- [ ] **Frontend build** — Vite build, served by nginx or Coolify static.
- [ ] **VITE_API_URL** → `https://saas.ahmethamdiozen.site/api/v1`.

### Operability

- [ ] **Expand `/health` endpoint** — DB ping + Redis ping + RQ registry count.
- [ ] **Structured JSON logging** — swap default Python logging format for `structlog` or `loguru` JSON output.
- [ ] **Graceful worker shutdown** — on SIGTERM, finish current job then exit. Don't kill mid-job.

### Demo data

- [ ] **Seed script** — demo user `demo@saas` / `demo1234`, one admin, one pre-indexed document with 5-10 pages (e.g., the project's own README as PDF).

---

## Phase 1 — Post-Deploy MVP Gaps

### Auth module

- [ ] **Email verification flow** — signup sends verification email (Resend/SendGrid), user can't upload docs until verified. Prevents quota-burn spam.
- [ ] **Password reset** — forgot password → email link → reset.
- [ ] **Refresh token rotation** — on refresh, revoke old refresh token, issue new one. Detect reuse as compromise.

### Jobs module

- [ ] **Job progress UI** — frontend polls (or SSE) `GET /api/v1/jobs/:id/progress` during ingestion. Progress bar + "processing page 3 of 10".
- [ ] **Cancel button** — already supported in backend (cancellation token); wire to UI.
- [ ] **Retry failed job button** — admin-only.
- [ ] **Job history page** — user sees all their past jobs with status, duration, result.

### RAG / Document Manager

- [ ] **Upload limits** — max 20 MB per file, max 10 files per free-tier user; configurable via env.
- [ ] **Document list + delete** — user can see their uploaded docs, delete them (cascade: remove from ChromaDB + delete file from disk/S3).
- [ ] **Source citations in answers** — response includes `{ answer, sources: [{ file, page, quote }] }`. Frontend renders citations.
- [ ] **Multi-document query scoping** — user picks which docs to query against; defaults to all of theirs.
- [ ] **Chat history persistence** — conversations stored in DB, resumable.

### Admin / observability

- [ ] **Admin dashboard** — total users, active users, jobs by status, storage used.
- [ ] **Rate limiting** — free tier: 20 queries/day, 5 uploads/day (Redis counter).
- [ ] **Sentry integration** for uncaught exceptions in API + worker.

### Subscriptions (if wired)

- [ ] **Stripe subscription plans** — Free vs Pro (higher quotas). Webhook handles subscription status sync.
- [ ] **Quota enforcement middleware** — checks user's plan before accepting requests that exceed free-tier limits.

---

## Phase 2 — Polish / Portfolio Readiness

- [ ] **Public demo account** — `demo@saas.ahmethamdiozen.site` / `demo1234` README, with a pre-seeded workspace so visitors see data immediately.
- [ ] **Screenshot pack** — landing, signup, document upload (with progress), RAG chat, admin dashboard, job queue.
- [ ] **90s video demo** — upload → job progress → ask question → see answer with citations.
- [ ] **Portfolio card on ahmethamdiozen.site**:
  - Title: "SaaS Framework + RAG Document Manager (Python)"
  - Tech: FastAPI, RQ, SQLAlchemy, Alembic, Redis, PostgreSQL, JWT, ChromaDB
  - Links: live app, GitHub, video
  - TR + EN copy
  - **Emphasize**: "polyglot — this one is Python, my other backends are TypeScript"
- [ ] **Architecture diagram in README** — `request → FastAPI → RQ enqueue → worker → embeddings + ChromaDB`.
- [ ] **API docs** — FastAPI auto-generates `/docs`; make sure it's accessible at `saas.ahmethamdiozen.site/api/v1/docs` with examples populated.
- [ ] **Landing page** — not just the app; a marketing-style page with pricing tiers (even if Stripe isn't wired yet, show intent).

### CI/CD

- [ ] **GitHub Actions**: lint (ruff), type-check (mypy), `pytest` on PR. Coolify webhook on main.
- [ ] **Alembic migration sanity check** — CI runs `alembic upgrade head` + `alembic downgrade -1` + `alembic upgrade head` on a fresh DB to catch bad migrations.
- [ ] **Test coverage report** — `pytest-cov` → codecov badge in README.

---

## Phase 3 — Stretch

- [ ] **Team workspaces** — invite users to shared doc workspaces; permissions (owner/editor/viewer).
- [ ] **Usage analytics** — per-user query count, popular docs, peak hours. Charts.
- [ ] **Model choice** — user picks embedding model (MiniLM vs BGE vs OpenAI) + LLM (GPT-4, Claude, local Ollama).
- [ ] **Ollama backend option** — swap OpenAI for local Ollama (reuse learnings from `rag-mvp`); toggleable via env.
- [ ] **Reranker** — add Cohere rerank or cross-encoder before final retrieval.
- [ ] **Audit log** — every user action stored (GDPR-friendly for EU).
- [ ] **Multi-region deploy** — eu-central vs us-east, proximity routing.

---

## Deploy Checklist (Coolify)

1. DNS: A record for `saas.ahmethamdiozen.site`.
2. Coolify Postgres + Redis resources (Redis doubles as RQ queue backend).
3. API service: `hf-saas-backend/Dockerfile`, port 8000, `BACKEND_CORS_ORIGINS`, `DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`, `OPENAI_API_KEY` (or equivalent).
4. Worker service: same image, command override `python -m app.worker.worker`, same env.
5. Frontend service: static, `hf-saas-frontend` → `dist/`, `VITE_API_URL=https://saas.ahmethamdiozen.site/api/v1`.
6. Reverse proxy: frontend at `/`, API at `/api/v1`.
7. Run `alembic upgrade head` + seed script.
8. Smoke: signup → login → upload PDF → verify job completes → ask question.

---

## Demo Setup

- Landing + app at `saas.ahmethamdiozen.site`.
- Demo user: `demo@saas.ahmethamdiozen.site` / `demo1234` — pre-seeded with a "Sample Policy.pdf" document indexed and ready to query.
- Admin: `admin@saas.ahmethamdiozen.site` / (separate password, not in public README).
- Rate limits on demo account clearly surfaced in UI.
