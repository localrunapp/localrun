"""
Database configuration and session management - SQLModel
"""

import logging
from pathlib import Path
from sqlmodel import create_engine, SQLModel, Session

from core.settings import settings
from core.logger import setup_logger

logger = setup_logger(__name__)

# SQLModel will automatically register models when they're imported elsewhere
# No need to import them here - this causes circular imports

# Ensure database directory exists
db_path = Path("./database")
db_path.mkdir(parents=True, exist_ok=True)

# Create SQLite engine
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},  # Needed for SQLite
    echo=False,  # Disable SQLAlchemy logging
)

# Disable SQLAlchemy logging
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.dialects").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.orm").setLevel(logging.WARNING)


def get_db():
    """Dependency to get database session."""
    with Session(engine) as session:
        yield session


# Alias for compatibility
get_session = get_db


def init_db():
    """Initialize database - create all tables."""
    logger.info("Initializing database...")
    SQLModel.metadata.create_all(engine)
    logger.info("Database initialized successfully")
