import datetime
import enum

from sqlalchemy.ext.declarative import declared_attr

from taiga2.sqlalchemy_mixins.base_mixin import BaseMixin
from taiga2.models import db, GUID, generate_uuid, User, Dataset


class Activity(db.Model, BaseMixin):
    class ActivityType(enum.Enum):
        created = "Created"
        changed_name = "Changed name"
        changed_description = "Changed Description"
        added_version = "Added version"
        started_log = "Log started"

    __tablename__ = "activities"

    id: str = db.Column(GUID, primary_key=True, default=generate_uuid)

    user_id: str = db.Column(GUID, db.ForeignKey("users.id"))

    user: User = db.relationship("User", backref=__tablename__)

    dataset_id: str = db.Column(GUID, db.ForeignKey("datasets.id"))

    dataset: Dataset = db.relationship("Dataset", backref=__tablename__)

    # We would want the type of change and the comments associated
    type: ActivityType = db.Column(db.Enum(ActivityType), nullable=False)

    timestamp: datetime.datetime = db.Column(
        db.DateTime, default=datetime.datetime.utcnow
    )

    comments: str = db.Column(db.Text)

    __mapper_args__ = {"polymorphic_on": type}


class CreationActivity(Activity):
    __mapper_args__ = {"polymorphic_identity": Activity.ActivityType.created}

    @declared_attr
    def dataset_name(cls) -> str:
        return Activity.__table__.c.get("dataset_name", db.Column(db.Text))

    @declared_attr
    def dataset_description(cls) -> str:
        return Activity.__table__.c.get("dataset_description", db.Column(db.Text))


class NameUpdateActivity(Activity):
    __mapper_args__ = {"polymorphic_identity": Activity.ActivityType.changed_name}

    @declared_attr
    def dataset_name(cls) -> str:
        return Activity.__table__.c.get("dataset_name", db.Column(db.Text))


class DescriptionUpdateActivity(Activity):
    __mapper_args__ = {
        "polymorphic_identity": Activity.ActivityType.changed_description
    }

    @declared_attr
    def dataset_description(cls) -> str:
        return Activity.__table__.c.get("dataset_description", db.Column(db.Text))

    @declared_attr
    def dataset_version(cls) -> int:
        return Activity.__table__.c.get("dataset_version", db.Column(db.Integer))


class VersionAdditionActivity(Activity):
    __mapper_args__ = {"polymorphic_identity": Activity.ActivityType.added_version}

    @declared_attr
    def dataset_description(cls) -> str:
        return Activity.__table__.c.get("dataset_description", db.Column(db.Text))

    @declared_attr
    def dataset_version(cls) -> str:
        return Activity.__table__.c.get("dataset_version", db.Column(db.Integer))


class LogStartActivity(Activity):
    __mapper_args__ = {"polymorphic_identity": Activity.ActivityType.started_log}

    @declared_attr
    def dataset_name(cls) -> str:
        return Activity.__table__.c.get("dataset_name", db.Column(db.Text))

    @declared_attr
    def dataset_description(cls) -> str:
        return Activity.__table__.c.get("dataset_description", db.Column(db.Text))

    @declared_attr
    def dataset_version(cls) -> str:
        return Activity.__table__.c.get("dataset_version", db.Column(db.Integer))
