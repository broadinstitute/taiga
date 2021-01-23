from flask_marshmallow import fields
from marshmallow_oneofschema import OneOfSchema

from taiga2.schemas import ma
from taiga2.activities.models import (
    Activity,
    CreationActivity,
    NameUpdateActivity,
    DescriptionUpdateActivity,
    VersionAdditionActivity,
    LogStartActivity,
)


class ActivityLogBaseSchema(ma.ModelSchema):
    class Meta:
        additional = ("id", "timestamp", "comments")

    user_name = fields.fields.Method("get_user_name")

    def get_user_name(self, obj):
        return obj.user.name


class CreationActivityLogSchema(ActivityLogBaseSchema):
    dataset_name = fields.fields.String()
    dataset_description = fields.fields.String()


class NameUpdateActivityLogSchema(ActivityLogBaseSchema):
    dataset_name = fields.fields.String()


class DescriptionUpdateActivityLogSchema(ActivityLogBaseSchema):
    dataset_description = fields.fields.String()
    dataset_version = fields.fields.Integer()


class VersionAdditionActivityLogSchema(ActivityLogBaseSchema):
    dataset_description = fields.fields.String()
    dataset_version = fields.fields.Integer()


class LogStartActivityLogSchema(ActivityLogBaseSchema):
    dataset_name = fields.fields.String()
    dataset_description = fields.fields.String()
    dataset_version = fields.fields.Integer()


class ActivityLogSchema(OneOfSchema):
    type_schemas = {
        Activity.ActivityType.created.name: CreationActivityLogSchema,
        Activity.ActivityType.changed_name.name: NameUpdateActivityLogSchema,
        Activity.ActivityType.changed_description.name: DescriptionUpdateActivityLogSchema,
        Activity.ActivityType.added_version.name: VersionAdditionActivityLogSchema,
        Activity.ActivityType.started_log.name: LogStartActivityLogSchema,
    }

    def get_obj_type(self, obj):
        return obj.type.name
