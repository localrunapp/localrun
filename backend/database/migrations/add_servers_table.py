from sqlmodel import Session, select
from core.database import engine
from app.models.server import Server
from app.models.user import User
from core.logger import setup_logger

logger = setup_logger(__name__)


def upgrade():
    """Run migration"""
    logger.info("Running migration: add_servers_table")

    # Import here to avoid circular imports
    from sqlmodel import SQLModel

    # Create servers table
    SQLModel.metadata.create_all(engine, tables=[Server.__table__])
    logger.info("Created servers table")

    # Create localhost server for each existing user
    with Session(engine) as session:
        users = session.exec(select(User)).all()

        for user in users:
            # Check if localhost already exists
            existing = session.exec(select(Server).where(Server.user_id == user.id, Server.is_local == True)).first()

            if not existing:
                localhost = Server(
                    name="localhost",
                    host="127.0.0.1",
                    description="Local machine",
                    is_local=True,
                    is_reachable=True,
                    user_id=user.id,
                )
                session.add(localhost)
                logger.info(f"Created localhost server for user {user.username}")

        session.commit()

    logger.info("Migration completed successfully")


def downgrade():
    """Rollback migration"""
    logger.info("Rolling back migration: add_servers_table")

    # Drop servers table
    Server.__table__.drop(engine)
    logger.info("Dropped servers table")

    logger.info("Rollback completed")


if __name__ == "__main__":
    upgrade()
