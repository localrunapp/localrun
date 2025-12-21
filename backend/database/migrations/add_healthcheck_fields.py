from sqlalchemy import text
from sqlmodel import Session
from core.database import engine
from core.logger import setup_logger

logger = setup_logger(__name__)


def upgrade():
    """Add healthcheck fields to services table"""
    logger.info("Running migration: add_healthcheck_fields")

    with Session(engine) as session:
        # Add healthcheck configuration columns
        session.exec(text("""
            ALTER TABLE services 
            ADD COLUMN IF NOT EXISTS healthcheck_enabled BOOLEAN DEFAULT TRUE
        """))
        
        session.exec(text("""
            ALTER TABLE services 
            ADD COLUMN IF NOT EXISTS healthcheck_path VARCHAR(255) DEFAULT '/'
        """))
        
        session.exec(text("""
            ALTER TABLE services 
            ADD COLUMN IF NOT EXISTS healthcheck_timeout INTEGER DEFAULT 5
        """))
        
        session.exec(text("""
            ALTER TABLE services 
            ADD COLUMN IF NOT EXISTS healthcheck_expected_status INTEGER DEFAULT 200
        """))
        
        # Add healthcheck status columns
        session.exec(text("""
            ALTER TABLE services 
            ADD COLUMN IF NOT EXISTS healthcheck_status VARCHAR(20) DEFAULT 'unknown'
        """))
        
        session.exec(text("""
            ALTER TABLE services 
            ADD COLUMN IF NOT EXISTS healthcheck_last_check TIMESTAMP
        """))
        
        session.exec(text("""
            ALTER TABLE services 
            ADD COLUMN IF NOT EXISTS healthcheck_last_error VARCHAR(500)
        """))
        
        session.exec(text("""
            ALTER TABLE services 
            ADD COLUMN IF NOT EXISTS healthcheck_consecutive_failures INTEGER DEFAULT 0
        """))
        
        session.commit()
        logger.info("Added healthcheck columns to services table")

    logger.info("Migration completed successfully")


def downgrade():
    """Remove healthcheck fields from services table"""
    logger.info("Rolling back migration: add_healthcheck_fields")

    with Session(engine) as session:
        session.exec(text("""
            ALTER TABLE services 
            DROP COLUMN IF EXISTS healthcheck_enabled,
            DROP COLUMN IF EXISTS healthcheck_path,
            DROP COLUMN IF EXISTS healthcheck_timeout,
            DROP COLUMN IF EXISTS healthcheck_expected_status,
            DROP COLUMN IF EXISTS healthcheck_status,
            DROP COLUMN IF EXISTS healthcheck_last_check,
            DROP COLUMN IF EXISTS healthcheck_last_error,
            DROP COLUMN IF EXISTS healthcheck_consecutive_failures
        """))
        
        session.commit()
        logger.info("Removed healthcheck columns from services table")

    logger.info("Rollback completed")


if __name__ == "__main__":
    upgrade()
