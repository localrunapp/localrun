import uuid

from sqlmodel import Session, select

from app.models.user import User
from app.models.config import Config
from core.database import engine, init_db
from core.hash import Hash
from core.logger import setup_logger

logger = setup_logger(__name__)


class DatabaseSeeder:
    """
    Main database seeder.
    """

    @staticmethod
    def run():
        """
        Run all seeders.
        """
        logger.info("Database setup...")

        with Session(engine) as db:
            try:
                # Run individual seeders
                initial_password = UserSeeder.run(db)
                ConfigSeeder.run(db)
                ServerSeeder.run(db)

                # Providers
                provider_count = ProviderSeeder.run(db)

                logger.info(
                    f"Database setup complete (providers: {', '.join(provider_count)})"
                )

                return initial_password
            except Exception as e:
                logger.error(f"Database seeding failed: {str(e)}")
                db.rollback()
                raise


class UserSeeder:
    """
    User seeder.
    """

    @staticmethod
    def run(db: Session) -> str:
        """Seed users table - creates admin with placeholder password"""
        # Check if admin user already exists
        statement = select(User).where(User.username == "admin")
        existing_user = db.exec(statement).first()

        if existing_user:
            return None

        # Create admin user with placeholder password (will be set during setup)
        admin_user = User(
            username="admin",
            email="admin@localrun.local",
            password=Hash.make("placeholder_password"),  # Will be replaced during setup
            full_name="System Administrator",
            is_active=True,
            is_admin=True,
        )

        db.add(admin_user)
        db.commit()

        return None  # No initial password to return


class ConfigSeeder:
    """
    Config seeder - creates initial config record.
    """

    @staticmethod
    def run(db: Session):
        """Seed configs table"""
        # Check if config already exists
        statement = select(Config)
        existing_config = db.exec(statement).first()

        if existing_config:
            return

        # Create initial config
        config = Config(
            setup_completed=False,
            installation_name=None,
            initial_password_used=False,
        )

        db.add(config)
        db.commit()


class ServerSeeder:
    """
    Server seeder - creates localhost server for each user.
    """

    @staticmethod
    def run(db: Session):
        """Seed servers table with localhost for each user"""
        from app.models.server import Server

        # Check if localhost already exists (global)
        server_statement = select(Server).where(Server.is_local == True)
        existing_server = db.exec(server_statement).first()

        if existing_server:
            return

        # Create localhost server
        localhost = Server(
            id=str(uuid.uuid4()),
            name="localhost",
            host="127.0.0.1",
            description="Local machine",
            is_local=True,
            is_reachable=True,
        )

        db.add(localhost)
        db.commit()


class ProviderSeeder:
    """
    Provider seeder - creates default providers.
    """

    @staticmethod
    def run(db: Session) -> list:
        """Seed providers table and return list of created providers"""
        from app.models.provider import Provider

        default_providers = [
            {
                "key": "cloudflare",
                "tunnel_name": "localrun-tunnel",
                "http": True,
                "dns": True,
                "tcp": True,
                "ssh": True,
                "is_active": True,
            },
            {
                "key": "ngrok",
                "tunnel_name": None,
                "http": True,
                "dns": False,
                "tcp": True,
                "ssh": False,
                "is_active": True,
            },
            {
                "key": "pinggy",
                "tunnel_name": None,
                "http": True,
                "dns": False,
                "tcp": True,
                "ssh": True,
                "is_active": True,
            },
        ]

        created = []
        for provider_data in default_providers:
            statement = select(Provider).where(Provider.key == provider_data["key"])
            existing = db.exec(statement).first()

            if not existing:
                provider = Provider(**provider_data)
                db.add(provider)
                created.append(provider_data["key"])

        db.commit()
        return created


def seed_database():
    """
    Convenience function to initialize and seed database.
    Laravel equivalent: php artisan migrate:fresh --seed
    """
    # Initialize database (create tables)
    init_db()

    # Run seeders (returns initial password if generated)
    initial_password = DatabaseSeeder.run()

    return initial_password
