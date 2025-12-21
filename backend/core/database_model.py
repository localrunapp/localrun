"""
Database Model Base - Active Record Pattern
Provides Laravel-style ORM methods for SQLModel entities.
"""

from sqlmodel import SQLModel, Session, select
from typing import TypeVar, Type, Optional, List, Dict, Any
from datetime import datetime
from core.database import engine

T = TypeVar("T", bound="DatabaseModel")


def get_engine():
    """Lazy import engine to avoid circular imports."""
    return engine


class DatabaseModel(SQLModel):
    """
    Base model with Active Record pattern (Laravel-style).

    All database models should inherit from this class to get
    automatic CRUD methods without needing to pass db sessions.

    Usage:
        # Create
        server = Server(name="My Server", host="192.168.1.1")
        server.save()

        # Or
        server = Server.create(name="My Server", host="192.168.1.1")

        # Find
        server = Server.find("server-id")

        # Update
        server.name = "Updated Name"
        server.save()

        # Delete
        server.delete()

        # Query
        servers = Server.all()
        servers = Server.where(is_reachable=True)
        server = Server.first_where(host="192.168.1.1")
    """

    def save(self: T) -> T:
        """
        Save (create or update) the model to database.
        Automatically handles insert vs update based on primary key.
        """
        with Session(get_engine()) as session:
            session.add(self)
            session.commit()
            session.refresh(self)
            return self

    def delete(self) -> bool:
        """Delete the model from database."""
        with Session(get_engine()) as session:
            # Need to merge first to attach to this session
            instance = session.merge(self)
            session.delete(instance)
            session.commit()
            return True

    def refresh(self: T) -> T:
        """Refresh model data from database."""
        with Session(get_engine()) as session:
            session.refresh(self)
            return self

    def update(self: T, **kwargs) -> T:
        """Update model attributes and save."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        return self.save()

    @classmethod
    def find(cls: Type[T], id: Any) -> Optional[T]:
        """Find a model by primary key ID."""
        with Session(get_engine()) as session:
            return session.get(cls, id)

    @classmethod
    def find_or_fail(cls: Type[T], id: Any) -> T:
        """Find a model by ID or raise exception."""
        instance = cls.find(id)
        if not instance:
            raise ValueError(f"{cls.__name__} with id {id} not found")
        return instance

    @classmethod
    def all(cls: Type[T]) -> List[T]:
        """Get all records."""
        with Session(get_engine()) as session:
            statement = select(cls)
            return list(session.exec(statement).all())

    @classmethod
    def where(cls: Type[T], **filters) -> List[T]:
        """
        Find records by filters.

        Example:
            Server.where(is_reachable=True, os_type="Linux")
        """
        with Session(get_engine()) as session:
            statement = select(cls)
            for key, value in filters.items():
                if hasattr(cls, key):
                    statement = statement.where(getattr(cls, key) == value)
            return list(session.exec(statement).all())

    @classmethod
    def first_where(cls: Type[T], **filters) -> Optional[T]:
        """Find first record matching filters."""
        results = cls.where(**filters)
        return results[0] if results else None

    @classmethod
    def create(cls: Type[T], **kwargs) -> T:
        """
        Create and save a new record.

        Example:
            server = Server.create(name="My Server", host="192.168.1.1")
        """
        instance = cls(**kwargs)
        return instance.save()

    @classmethod
    def get_or_create(
        cls: Type[T], defaults: Dict[str, Any] = None, **filters
    ) -> tuple[T, bool]:
        """
        Get existing record or create new one.

        Returns:
            Tuple of (instance, created) where created is True if new record was created
        """
        instance = cls.first_where(**filters)
        if instance:
            return instance, False

        create_data = {**filters, **(defaults or {})}
        return cls.create(**create_data), True

    @classmethod
    def count(cls: Type[T]) -> int:
        """Count all records."""
        with Session(engine) as session:
            statement = select(cls)
            return len(list(session.exec(statement).all()))

    @classmethod
    def exists(cls: Type[T], **filters) -> bool:
        """Check if any record exists matching filters."""
        return cls.first_where(**filters) is not None

    @classmethod
    def delete_where(cls: Type[T], **filters) -> int:
        """Delete all records matching filters. Returns count of deleted records."""
        records = cls.where(**filters)
        count = len(records)
        for record in records:
            record.delete()
        return count
