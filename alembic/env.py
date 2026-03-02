from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# 1. Import Base
from app.db.base import Base
# 2. Import Settings
from app.core.config import settings

# 3. Import ALL models here so Alembic can see them for autogenerate
from app.modules.users.models import User
from app.modules.auth.models import RefreshToken
from app.modules.subscriptions.models import Subscription, UserSubscription
from app.modules.jobs.models import Job, JobResult, JobExecution
from app.modules.rag.models import Document, Project, ChatSession, ChatMessage

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
