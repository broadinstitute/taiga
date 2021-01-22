from typing import List, Optional, Tuple, TypeVar, Type

from flask import abort
from taiga2.extensions import db


# "Generic" type
T = TypeVar("T", bound="BaseMixin")


class BaseMixin(object):
    _repr_hide = ["created_at", "updated_at"]

    @classmethod
    def query(cls):
        return db.session.query(cls)

    @classmethod
    def get(cls: Type[T], id: str) -> T:
        return cls.query.get(id)

    @classmethod
    def get_by(cls: Type[T], **kw) -> Optional[T]:
        return cls.query.filter_by(**kw).one_or_none()

    @classmethod
    def get_all_by(cls: Type[T], **kw) -> List[T]:
        return cls.query.filter_by(**kw).all()

    @classmethod
    def get_or_create(cls: Type[T], **kw) -> Tuple[T, bool]:
        r = cls.get_by(**kw)
        is_new = False
        if not r:
            is_new = True
            r = cls(**kw)
            db.session.add(r)

        return r, is_new

    @classmethod
    def create(cls: Type[T], **kw) -> T:
        r = cls(**kw)
        db.session.add(r)
        return r

    def save(self):
        db.session.add(self)

    def delete(self):
        db.session.delete(self)
