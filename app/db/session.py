from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Optimized for Cloud DBs (Supabase/Neon)
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=10,          # Increased pool size
    max_overflow=20,       # Allow more temporary connections
    pool_timeout=30,       # Wait up to 30s for a connection
    pool_recycle=1800,     # Reset connections every 30 mins to avoid stale links
)

SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False,
    bind=engine
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
