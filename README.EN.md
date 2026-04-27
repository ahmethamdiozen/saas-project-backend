[🇹🇷 Türkçe](README.md)

# SaaS Backend Framework

A production-ready SaaS backend built with FastAPI, SQLAlchemy, and Redis Queue (RQ). Implements a modular architecture with a focus on background job processing, reliability, and observability.

## Features

- **FastAPI** — async REST API with auto-generated Swagger docs
- **Background Jobs** — Redis Queue (RQ) with progress tracking, cancellation tokens, and automatic retries
- **Distributed Locking** — prevents duplicate job execution across workers
- **JWT Auth** — access + refresh token pattern with bcrypt password hashing
- **Database Migrations** — Alembic for versioned schema management
- **Observability** — structured logging, global exception handler, health check endpoint

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI |
| Database | PostgreSQL (SQLAlchemy ORM) |
| Task Queue | Redis + RQ (Redis Queue) |
| Migrations | Alembic |
| Validation | Pydantic v2 |

## Project Structure

```
app/
├── core/           # Logging, security, config
├── db/             # Database session and base models
├── modules/        # Domain-driven modules (Auth, Users, Jobs, Subscriptions)
│   └── [module]/   # router, service, repository, models, schemas
├── worker/         # Background worker, tasks, cancellation
└── tests/          # Unit and integration tests
```

## Getting Started

```bash
git clone https://github.com/ahmethamdiozen/saas-project-backend.git
cd saas-project-backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Create `.env`:
```env
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/saas_db
SECRET_KEY=your-secret-key
REDIS_URL=redis://localhost:6379/0
BACKEND_CORS_ORIGINS=http://localhost:3000
```

```bash
alembic upgrade head
uvicorn app.main:app --reload        # API on :8000
python -m app.worker.worker          # Background worker
```

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Testing

```bash
pytest
```

## License

MIT
