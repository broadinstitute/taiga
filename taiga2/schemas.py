from flask_marshmallow import Marshmallow, fields
from marshmallow import post_dump
from marshmallow_enum import EnumField
from marshmallow_oneofschema import OneOfSchema

from taiga2.models import (
    User,
    Folder,
    Entry,
    Dataset,
    DatasetVersion,
    DataFile,
    S3DataFile,
    get_allowed_conversion_type,
    resolve_virtual_datafile,
    Activity,
    CreationActivity,
    NameUpdateActivity,
    DescriptionUpdateActivity,
    VersionAdditionActivity,
    LogStartActivity,
)
from taiga2.models import ProvenanceEdge, ProvenanceNode, ProvenanceGraph
from taiga2.models import Group, EntryRightsEnum

ma = Marshmallow()


class UserSchema(ma.ModelSchema):
    class Meta:
        fields = ("id", "name", "home_folder_id", "trash_folder_id", "token")


class UserNamedIdSchema(ma.ModelSchema):
    class Meta:
        fields = ("id", "name")


class FolderNamedIdSchema(ma.ModelSchema):
    class Meta:
        fields = ("id", "name")


class DatasetNamedIdSchema(ma.ModelSchema):
    class Meta:
        fields = ("id", "name")


class DatasetSummarySchema(ma.ModelSchema):
    class Meta:
        additional = ("id", "permaname")

    permanames = fields.fields.Method("ordered_permanames")

    def ordered_permanames(self, dataset):
        permanames = sorted(
            dataset.permanames, key=lambda permaname: permaname.creation_date
        )
        return [permaname.permaname for permaname in permanames]


class DatasetVersionSummarySchema(ma.ModelSchema):
    class Meta:
        additional = ("id", "name")

    state = EnumField(DatasetVersion.DatasetVersionState)


class EntrySummarySchema(ma.ModelSchema):
    class Meta:
        fields = ("id", "name", "type")


class EntrySchema(ma.ModelSchema):
    # TODO: We need to rethink this because Entry is not (yet?) aware about all these attributes
    # TODO: A dataset does not have a creator because the dataset version has...should we print the creator of the last datasetVersion?
    class Meta:
        fields = ("type", "id", "name", "creation_date", "creator")

    creator = ma.Nested(UserNamedIdSchema)
    type = fields.fields.Method("get_lowercase_type")

    # TODO: Consolidate the type enum either by changing the model or by changing api+frontend
    def get_lowercase_type(self, obj):
        if isinstance(obj, Folder):
            return "folder"
        elif isinstance(obj, Dataset):
            return "dataset"
        elif isinstance(obj, DatasetVersion):
            return "dataset_version"
        else:
            raise Exception("Object with unexpected type: {}".format(type(obj)))


class FolderSchema(ma.ModelSchema):
    class Meta:
        # We just don't take the folder_type because of the Enum
        additional = (
            "id",
            "name",
            "type",
            "description",
            "entries",
            "creator",
            "creation_date",
            "parents",
        )

    # `Method` takes a method name (str), Function takes a callable
    can_edit = fields.fields.Method("check_edition")
    can_view = fields.fields.Method("check_view")

    entries = ma.Nested(EntrySchema, many=True)
    creator = ma.Nested(UserNamedIdSchema)
    folder_type = EnumField(Folder.FolderType)
    parents = ma.Nested(FolderNamedIdSchema, many=True)

    def check_edition(self, folder):
        """Check with the context if we can edit"""
        return self.context["entry_user_right"] == EntryRightsEnum.can_edit

    def check_view(self, folder):
        """Check if we can view by looking at the context of the entry. If can_edit, we can view too"""
        entry_user_right = self.context["entry_user_right"]
        return (
            entry_user_right == EntryRightsEnum.can_view
            or entry_user_right == EntryRightsEnum.can_edit
        )


class ProvenanceEdgeSchema(ma.ModelSchema):
    class Meta:
        fields = ("edge_id", "from_node_id", "to_node_id", "label")


class ProvenanceNodeWithEdgeSchema(ma.ModelSchema):
    class Meta:
        additional = ("node_id", "label", "datafile_id")

    from_edges = ma.Nested(ProvenanceEdgeSchema(), many=True)
    to_edges = ma.Nested(ProvenanceEdgeSchema(), many=True)
    type = EnumField(ProvenanceNode.NodeType)


class ProvenanceGraphFullSchema(ma.ModelSchema):
    class Meta:
        additional = (
            "graph_id",
            "permaname",
            "name",
            "created_by_user_id",
            "created_timestamp",
        )

    provenance_nodes = ma.Nested(ProvenanceNodeWithEdgeSchema(), many=True)


class ProvenanceGraphSchema(ma.ModelSchema):
    class Meta:
        fields = ("graph_id", "permaname", "name")


class ProvenanceNodeSchema(ma.ModelSchema):
    class Meta:
        fields = ("node_id", "graph")

    graph = ma.Nested(ProvenanceGraphSchema)


class DatasetVersionLightSchema(ma.ModelSchema):
    class Meta:
        additional = (
            "id",
            "name",
            "dataset_id",
            "creation_date",
            "creator",
            "description",
            "version",
            "reason_state",
        )

    creator = ma.Nested(UserNamedIdSchema)
    state = EnumField(DatasetVersion.DatasetVersionState)


class DatasetSchema(ma.ModelSchema):
    class Meta:
        additional = ("id", "name", "permaname", "dataset_versions", "parents")

    # TODO: Change this field to properly handle multiple permanames (a new permaname is added when we change the name of the dataset)
    permaname = fields.fields.Function(
        lambda obj: [obj.permaname], dump_to="permanames"
    )
    dataset_versions = ma.Nested(
        DatasetVersionSummarySchema, many=True, dump_to="versions"
    )
    parents = ma.Nested(FolderNamedIdSchema, dump_to="folders", many=True)

    # TODO: Repetitions of how we manage can_edit and can_view over the Schema, could make a superclass instead
    # `Method` takes a method name (str), Function takes a callable
    can_edit = fields.fields.Method("check_edition")
    can_view = fields.fields.Method("check_view")

    def check_edition(self, dataset):
        """Check with the context if we can edit"""
        return self.context["entry_user_right"] == EntryRightsEnum.can_edit

    def check_view(self, dataset):
        """Check if we can view by looking at the context of the entry. If can_edit, we can view too"""
        entry_user_right = self.context["entry_user_right"]
        return (
            entry_user_right == EntryRightsEnum.can_view
            or entry_user_right == EntryRightsEnum.can_edit
        )

    description = fields.fields.Method("description_str")

    def description_str(self, dataset):
        if dataset.description is None:
            return ""
        else:
            return dataset.description


class DataFileSummarySchema(ma.ModelSchema):
    class Meta:
        additional = ("name", "type", "short_summary")

    # TODO: Manage the other fields in the model/db too
    type = EnumField(S3DataFile.DataFileFormat)


class DataFileBaseSchema(ma.ModelSchema):
    class Meta:
        additional = ("id", "name")


class S3DataFileSchema(DataFileBaseSchema):
    s3_bucket = fields.fields.String()
    s3_key = fields.fields.String()
    short_summary = fields.fields.String()
    original_file_sha256 = fields.fields.String()

    # rename format -> type because that's what the existing client api expects
    type = fields.fields.Method("_get_type")
    allowed_conversion_type = fields.fields.Method("_get_allowed_conversion_type")

    def _get_type(self, data_file):
        return data_file.format.name

    def _get_allowed_conversion_type(self, data_file: DataFile):
        return get_allowed_conversion_type(data_file.format)


class VirtualDataFileSchema(DataFileBaseSchema):
    underlying_file_id = fields.fields.String()
    short_summary = fields.fields.String()

    # rename format -> type because that's what the existing client api expects
    type = fields.fields.Method("_get_type")
    allowed_conversion_type = fields.fields.Method("_get_allowed_conversion_type")
    gcs_path = fields.fields.Method("_get_gcs_path")

    def _get_type(self, data_file):
        return data_file.format.name

    def _get_allowed_conversion_type(self, data_file: DataFile):
        actual_datafile = resolve_virtual_datafile(data_file)
        if actual_datafile.type == "s3":
            return get_allowed_conversion_type(actual_datafile.format)
        return []

    def _get_gcs_path(self, data_file: DataFile):
        actual_datafile = resolve_virtual_datafile(data_file)
        if actual_datafile.type == "gcs":
            return actual_datafile.gcs_path
        return None


class GCSObjectDataFileSchema(DataFileBaseSchema):
    gcs_path = fields.fields.String()
    allowed_conversion_type = fields.fields.Method("_get_allowed_conversion_type")

    def _get_allowed_conversion_type(self, data_file: DataFile):
        return []


class DataFileSchema(OneOfSchema):
    type_field = "datafile_type"
    type_schemas = {
        "s3": S3DataFileSchema,
        "virtual": VirtualDataFileSchema,
        "gcs": GCSObjectDataFileSchema,
    }

    def get_obj_type(self, obj):
        return obj.type


class DatasetVersionSchema(ma.ModelSchema):
    class Meta:
        # WARNING: long_summary is pretty heavy. Don't include it here, but create your own schema
        additional = (
            "id",
            "name",
            "dataset_id",
            "creation_date",
            "creator",
            "datafiles",
            "parents",
            "changes_description",
        )

    creator = ma.Nested(UserNamedIdSchema)
    datafiles = ma.Nested(DataFileSchema, many=True)
    # TODO: Consolidate the term between folders and parents
    parents = ma.Nested(FolderNamedIdSchema, dump_to="folders", many=True)
    state = EnumField(DatasetVersion.DatasetVersionState)

    # TODO: Repetitions of how we manage can_edit and can_view over the Schema, could make a superclass instead
    # `Method` takes a method name (str), Function takes a callable
    can_edit = fields.fields.Method("check_edition")
    can_view = fields.fields.Method("check_view")
    version = fields.fields.Method("version_as_str")
    reason_state = fields.fields.Method("reason_state_str")
    description = fields.fields.Method("description_str")

    def description_str(self, dataset_version):
        if dataset_version.description is None:
            return ""
        else:
            return dataset_version.description

    def check_edition(self, dataset_version):
        """Check with the context if we can edit"""
        return self.context["entry_user_right"] == EntryRightsEnum.can_edit

    def check_view(self, dataset_version):
        """Check if we can view by looking at the context of the entry. If can_edit, we can view too"""
        entry_user_right = self.context["entry_user_right"]
        return (
            entry_user_right == EntryRightsEnum.can_view
            or entry_user_right == EntryRightsEnum.can_edit
        )

    def version_as_str(self, dataset_version):
        return str(dataset_version.version)

    def reason_state_str(self, dataset_version):
        reason_state = dataset_version.reason_state
        if reason_state is None:
            return ""
        else:
            return reason_state


class DatasetFullSchema(ma.ModelSchema):
    # TODO: Change the name to DatasetWithVersionSchema, because we skip a few fields
    class Meta:
        additional = ("id", "name", "description", "permaname", "dataset_versions")

    permanames = fields.fields.Method("ordered_permanames")

    dataset_versions = ma.Nested(
        DatasetVersionLightSchema(), many=True, dump_to="versions"
    )

    description = fields.fields.Method("description_str")

    def description_str(self, dataset_version):
        if dataset_version.description is None:
            return ""
        else:
            return dataset_version.description

    def ordered_permanames(self, dataset):
        permanames = sorted(
            dataset.permanames, key=lambda permaname: permaname.creation_date
        )
        return [permaname.permaname for permaname in permanames]

    # parents = ma.Nested(FolderNamedIdSchema(), dump_to='folders', many=True)


class AccessLogSchema(ma.ModelSchema):
    class Meta:
        additional = ("user_id", "entry", "last_access")

    entry = ma.Nested(EntrySummarySchema)
    user_name = fields.fields.Method("get_user_name")

    def get_user_name(self, obj):
        return obj.user.name


# <editor-fold desc="Search">
class BreadcrumbSchema(ma.ModelSchema):
    class Meta:
        additional = ("order",)

    folder = ma.Nested(FolderNamedIdSchema)


class SearchEntrySchema(ma.ModelSchema):
    entry = ma.Nested(EntrySchema)
    breadcrumbs = ma.Nested(BreadcrumbSchema, many=True)


class SearchResultSchema(ma.ModelSchema):
    class Meta:
        additional = ("name",)

    current_folder = ma.Nested(FolderNamedIdSchema)
    entries = ma.Nested(SearchEntrySchema, many=True)


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


class GroupSchema(ma.ModelSchema):
    class Meta:
        additional = ("id", "name")

    users = ma.Nested(UserNamedIdSchema, many=True)
    num_users = fields.fields.Method("get_num_users")

    def get_num_users(self, obj):
        return len(obj.users)


# </editor-fold>
