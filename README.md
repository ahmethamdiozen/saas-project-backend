# SaaS Backend Framework

A robust, production-ready SaaS backend built with **FastAPI**, **SQLAlchemy**, and **Redis Queue (RQ)**. This project implements a modular architecture with a focus on background job processing, reliability, and observability.

## 🚀 Features

- **Asynchronous API**: Built with FastAPI for high performance.
- **Robust Worker System**: 
  - Background task processing with Redis Queue (RQ).
  - Advanced Job Management: Progress tracking, cancellation tokens, and automatic retries.
  - Distributed Locking: Prevents duplicate job execution.
- **Security**: 
  - JWT-based Authentication (Access & Refresh Tokens).
  - Password hashing with Passlib.
  - CORS Middleware ready for frontend integration.
- **Database & Migrations**: 
  - SQLAlchemy ORM for database interactions.
  - Alembic for versioned database migrations.
- **Observability**: 
  - Structured logging across API and Worker.
  - Global Exception Handling for consistent error responses.
  - Health check endpoint for infrastructure monitoring.

## 🛠 Tech Stack

- **Framework**: [FastAPI](https://fastapi.tiangolo.com/)
- **Database**: [PostgreSQL](https://www.postgresql.org/) (via SQLAlchemy)
- **Task Queue**: [Redis](https://redis.io/) + [RQ (Redis Queue)](https://python-rq.org/)
- **Migrations**: [Alembic](https://alembic.sqlalchemy.org/)
- **Validation**: [Pydantic v2](https://docs.pydantic.dev/)

## 📂 Project Structure

```text
app/
├── core/           # Global configurations (logging, security, config)
├── db/             # Database session and base models
├── modules/        # Domain-driven modules (Auth, Users, Jobs, Subscriptions)
│   └── [module]/   # router, service, repository, models, schemas
├── worker/         # Background worker logic, tasks, and cancellation
└── tests/          # Unit and integration tests (organized by module)
```

## ⚙️ Getting Started

### Prerequisites

- Python 3.10+
- Redis (for background jobs)
- PostgreSQL (for data storage)

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd saas_backend
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up Environment Variables**:
   Create a `.env` file in the root directory:
   ```env
   DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/saas_db
   SECRET_KEY=your-super-secret-key
   REDIS_URL=redis://localhost:6379/0
   BACKEND_CORS_ORIGINS=http://localhost:3000,https://your-app.com
   ```

5. **Run Database Migrations**:
   ```bash
   alembic upgrade head
   ```

### Running the Application

**Start the API Server**:
```bash
uvicorn app.main:app --reload
```
The API will be available at `http://localhost:8000`.

**Start the Worker**:
```bash
python -m app.worker.worker
```

## 📖 API Documentation

Once the server is running, you can access the interactive documentation:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

All API endpoints are prefixed with `/api/v1`.

## 🧪 Testing

Run tests using pytest:
```bash
pytest
```

## 📝 License

This project is licensed under the MIT License.
