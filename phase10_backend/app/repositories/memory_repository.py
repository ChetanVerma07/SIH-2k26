"""
In-memory repository.

This is the storage abstraction for Phase 10. It is intentionally simple
(plain dicts keyed by ID) so it can later be swapped for a real database
(e.g. PostgreSQL via SQLAlchemy) WITHOUT changing any route or service code,
as long as the same method signatures are preserved.
"""
import uuid
from typing import Dict, Generic, List, Optional, TypeVar

T = TypeVar("T")


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class InMemoryRepository(Generic[T]):
    """Generic key-value store keyed by entity id."""

    def __init__(self):
        self._store: Dict[str, T] = {}

    def add(self, entity_id: str, entity: T) -> T:
        self._store[entity_id] = entity
        return entity

    def get(self, entity_id: str) -> Optional[T]:
        return self._store.get(entity_id)

    def list(self) -> List[T]:
        return list(self._store.values())

    def delete(self, entity_id: str) -> bool:
        if entity_id in self._store:
            del self._store[entity_id]
            return True
        return False

    def exists(self, entity_id: str) -> bool:
        return entity_id in self._store

    def clear(self) -> None:
        self._store.clear()


class RepositoryRegistry:
    """
    Holds one InMemoryRepository per entity type.

    A single shared instance is used across the app (see dependencies.py),
    simulating a persistence layer without requiring a real database.
    """

    def __init__(self):
        self.projects: InMemoryRepository = InMemoryRepository()
        self.designs: InMemoryRepository = InMemoryRepository()
        self.climate_records: InMemoryRepository = InMemoryRepository()
        self.materials: InMemoryRepository = InMemoryRepository()
        self.simulations: InMemoryRepository = InMemoryRepository()
        self.optimizations: InMemoryRepository = InMemoryRepository()

    def reset(self) -> None:
        self.projects.clear()
        self.designs.clear()
        self.climate_records.clear()
        self.materials.clear()
        self.simulations.clear()
        self.optimizations.clear()


# Single shared instance for the whole application (acts like a DB connection pool)
repository_registry = RepositoryRegistry()
