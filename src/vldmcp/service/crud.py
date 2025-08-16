"""CRUD service base class for data-driven services."""

from typing import Type, Any
from datetime import datetime, UTC
from sqlmodel import SQLModel, create_engine, Session, select

from .base import Service
from .system.storage import Storage


class CRUDService(Service):
    """Base service that provides CRUD operations for SQLModel classes."""

    def __init__(self, storage: Storage, models: list[Type[SQLModel]], parent=None, name=None):
        super().__init__(parent, name)
        self.storage = storage

        # Create database path and engine
        db_path = storage.database_path("service")
        db_path.parent.mkdir(parents=True, exist_ok=True)

        # SQLite connection string
        self.engine = create_engine(f"sqlite:///{db_path}")

        # Store models by lowercase name for easy access
        self.models = {}
        for model in models:
            model_name = model.__name__.lower()
            self.models[model_name] = model

            # Make model accessible as attribute
            setattr(self, model_name, model)

        # Create all tables
        SQLModel.metadata.create_all(self.engine)

    def get_session(self) -> Session:
        """Get a database session."""
        return Session(self.engine)

    def create(self, model_name: str, **kwargs) -> Any:
        """Create a new record."""
        if model_name not in self.models:
            raise ValueError(f"Unknown model: {model_name}")

        model_class = self.models[model_name]
        instance = model_class(**kwargs)

        with self.get_session() as session:
            session.add(instance)
            session.commit()
            session.refresh(instance)
            return instance

    def read(self, model_name: str, **filters) -> list[Any]:
        """Read records with optional filtering."""
        if model_name not in self.models:
            raise ValueError(f"Unknown model: {model_name}")

        model_class = self.models[model_name]

        with self.get_session() as session:
            query = select(model_class)

            # Apply filters
            for field, value in filters.items():
                if hasattr(model_class, field):
                    query = query.where(getattr(model_class, field) == value)

            return session.exec(query).all()

    def update(self, model_name: str, filters: dict, updates: dict) -> int:
        """Update records matching filters."""
        if model_name not in self.models:
            raise ValueError(f"Unknown model: {model_name}")

        model_class = self.models[model_name]

        with self.get_session() as session:
            query = select(model_class)

            # Apply filters
            for field, value in filters.items():
                if hasattr(model_class, field):
                    query = query.where(getattr(model_class, field) == value)

            # Get matching records
            records = session.exec(query).all()

            # Automatically set updated_at if the model has it
            if hasattr(model_class, "updated_at"):
                updates["updated_at"] = datetime.now(UTC)

            # Update each record
            count = 0
            for record in records:
                for key, value in updates.items():
                    if hasattr(record, key):
                        setattr(record, key, value)
                count += 1

            session.commit()
            return count

    def delete(self, model_name: str, **filters) -> int:
        """Delete records matching filters."""
        if model_name not in self.models:
            raise ValueError(f"Unknown model: {model_name}")

        model_class = self.models[model_name]

        with self.get_session() as session:
            query = select(model_class)

            # Apply filters
            for field, value in filters.items():
                if hasattr(model_class, field):
                    query = query.where(getattr(model_class, field) == value)

            # Get and delete records
            records = session.exec(query).all()
            count = len(records)
            for record in records:
                session.delete(record)

            session.commit()
            return count

    def upsert(self, model_name: str, unique_fields: list[str], **kwargs) -> Any:
        """Insert or update a record based on unique fields.

        Args:
            model_name: Name of the model
            unique_fields: Fields that determine uniqueness
            **kwargs: Data for the record

        Returns:
            The created or updated instance
        """
        if model_name not in self.models:
            raise ValueError(f"Unknown model: {model_name}")

        model_class = self.models[model_name]

        with self.get_session() as session:
            # Build filter for existing record
            filters = {}
            for field in unique_fields:
                if field in kwargs:
                    filters[field] = kwargs[field]

            # Try to find existing record
            query = select(model_class)
            for field, value in filters.items():
                if hasattr(model_class, field):
                    query = query.where(getattr(model_class, field) == value)

            existing = session.exec(query).first()

            if existing:
                # Update existing record
                if hasattr(model_class, "updated_at"):
                    kwargs["updated_at"] = datetime.now(UTC)

                for key, value in kwargs.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)

                session.commit()
                session.refresh(existing)
                return existing
            else:
                # Create new record
                instance = model_class(**kwargs)
                session.add(instance)
                session.commit()
                session.refresh(instance)
                return instance

    def get_records_since(self, model_name: str, since: datetime) -> list[Any]:
        """Get records updated since a given timestamp.

        Useful for incremental sync operations.
        """
        if model_name not in self.models:
            raise ValueError(f"Unknown model: {model_name}")

        model_class = self.models[model_name]

        # Only works if model has updated_at field
        if not hasattr(model_class, "updated_at"):
            raise ValueError(f"Model {model_name} does not have updated_at field")

        with self.get_session() as session:
            query = select(model_class)
            query = query.where(getattr(model_class, "updated_at") > since)
            return session.exec(query).all()
