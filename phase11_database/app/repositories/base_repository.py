"""
Generic CRUD base. Concrete repositories subclass this and add
domain-specific query methods. Repositories never commit/rollback on
their own beyond flush()+refresh() for getting generated defaults back;
transaction boundaries are owned by the caller (typically the
`get_session()` context manager in app.core.database, or later the
FastAPI service layer).
"""
from __future__ import annotations

import uuid
from typing import Generic, List, Optional, Type, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    model: Type[ModelT]

    def __init__(self, session: Session):
        self.session = session

    def create(self, **kwargs) -> ModelT:
        obj = self.model(**kwargs)
        self.session.add(obj)
        self.session.flush()
        self.session.refresh(obj)
        return obj

    def get(self, id_: uuid.UUID) -> Optional[ModelT]:
        return self.session.get(self.model, id_)

    def get_or_404(self, id_: uuid.UUID) -> ModelT:
        obj = self.get(id_)
        if obj is None:
            raise LookupError(f"{self.model.__name__} with id={id_} not found")
        return obj

    def list(self, limit: int = 100, offset: int = 0) -> List[ModelT]:
        stmt = select(self.model).limit(limit).offset(offset)
        return list(self.session.execute(stmt).scalars().all())

    def update(self, id_: uuid.UUID, **kwargs) -> ModelT:
        obj = self.get_or_404(id_)
        for key, value in kwargs.items():
            setattr(obj, key, value)
        self.session.flush()
        self.session.refresh(obj)
        return obj

    def delete(self, id_: uuid.UUID) -> None:
        obj = self.get_or_404(id_)
        self.session.delete(obj)
        self.session.flush()
