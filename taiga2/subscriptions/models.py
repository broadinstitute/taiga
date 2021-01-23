from typing import Dict, List, Optional, Tuple
import uuid

from sqlalchemy.orm import backref

from taiga2.extensions import db
from taiga2.models import User, Dataset, generate_uuid
from taiga2.sqlalchemy_mixins.base_mixin import BaseMixin


GUID = db.String(80)


class DatasetSubscription(db.Model, BaseMixin):
    __tablename__ = "dataset_subscriptions"

    id: str = db.Column(GUID, primary_key=True, default=generate_uuid)
    user: User = db.relationship("User", backref=__tablename__)
    user_id: str = db.Column(GUID, db.ForeignKey("users.id"))

    dataset: Dataset = db.relationship("Dataset", backref=__tablename__)
    dataset_id: str = db.Column(GUID, db.ForeignKey("datasets.id"))

    @classmethod
    def get_all_for_current_user(cls, user: User) -> List["DatasetSubscription"]:
        from taiga2.controllers.models_controller import get_current_session_user

        current_user = get_current_session_user()

        return cls.get_all_by(user_id=current_user.id)

    @classmethod
    def get_for_dataset_and_current_user(
        cls, dataset: Dataset
    ) -> Optional["DatasetSubscription"]:
        from taiga2.controllers.models_controller import get_current_session_user

        current_user = get_current_session_user()

        return cls.get_by(dataset_id=dataset.id, user_id=current_user.id)
