from flask_marshmallow import Marshmallow, fields
from marshmallow import post_dump
from marshmallow_enum import EnumField
from marshmallow_oneofschema import OneOfSchema

from taiga2.models import User, Folder, Entry, Dataset, DatasetVersion, DataFile, get_allowed_conversion_type
from taiga2.models import ProvenanceEdge, ProvenanceNode, ProvenanceGraph

ma = Marshmallow()


class UserSchema(ma.ModelSchema):
    class Meta:
        fields = ('id', 'name',
                  'home_folder_id', 'trash_folder_id',
                  'token')


class UserNamedIdSchema(ma.ModelSchema):
    class Meta:
        fields = ('id', 'name')


class FolderNamedIdSchema(ma.ModelSchema):
    class Meta:
        fields = ('id', 'name')


class DatasetNamedIdSchema(ma.ModelSchema):
    class Meta:
        fields = ('id', 'name')


class DatasetSummarySchema(ma.ModelSchema):
    class Meta:
        additional = ('id', 'permaname')

    permaname = fields.fields.Function(lambda obj: [obj.permaname], dump_to='permanames')


class DatasetVersionSummarySchema(ma.ModelSchema):
    # TODO: Add status later
    class Meta:
        fields = ('id', 'name')


class EntrySummarySchema(ma.ModelSchema):
    class Meta:
        fields = ('id', 'name', 'type')


class EntrySchema(ma.ModelSchema):
    # TODO: We need to rethink this because Entry is not (yet?) aware about all these attributes
    # TODO: A dataset does not have a creator because the dataset version has...should we print the creator of the last datasetVersion?
    class Meta:
        fields = ('type', 'id', 'name', 'creation_date',
                  'creator')

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


class FolderSchema(ma.ModelSchema):
    # TODO: Add the ACL
    class Meta:
        # We just don't take the folder_type because of the Enum
        additional = ('id', 'name', 'type', 'description',
                      'entries', 'creator', 'creation_date',
                      'parents')

    entries = ma.Nested(EntrySchema, many=True)
    creator = ma.Nested(UserNamedIdSchema)
    folder_type = EnumField(Folder.FolderType)
    parents = ma.Nested(FolderNamedIdSchema, many=True)

    # TODO: See how it has been resolved in Marshmallow. Temp workaround
    def dispatch_entries(self, obj):
        list_entries = []
        entry_schema = EntrySchema()

        return list_entries


class ProvenanceEdgeSchema(ma.ModelSchema):
    class Meta:
        fields = ('edge_id', 'from_node_id', 'to_node_id',
                  'label')


class ProvenanceNodeWithEdgeSchema(ma.ModelSchema):
    class Meta:
        additional = ('node_id', 'label', 'datafile_id')

    from_edges = ma.Nested(ProvenanceEdgeSchema(), many=True)
    to_edges = ma.Nested(ProvenanceEdgeSchema(), many=True)
    type = EnumField(ProvenanceNode.NodeType)


class ProvenanceGraphFullSchema(ma.ModelSchema):
    class Meta:
        additional = ('graph_id', 'permaname', 'name',
                      'created_by_user_id', 'created_timestamp')

    provenance_nodes = ma.Nested(ProvenanceNodeWithEdgeSchema(), many=True)


class ProvenanceGraphSchema(ma.ModelSchema):
    class Meta:
        fields = ('graph_id', 'permaname', 'name')


class ProvenanceNodeSchema(ma.ModelSchema):
    class Meta:
        fields = ('node_id', 'graph')

    graph = ma.Nested(ProvenanceGraphSchema)


class DatasetSchema(ma.ModelSchema):
    class Meta:
        additional = ('id', 'name', 'description',
                      'permaname', 'dataset_versions', 'parents')

    # TODO: Change this field to properly handle multiple permanames (a new permaname is added when we change the name of the dataset)
    permaname = fields.fields.Function(lambda obj: [obj.permaname], dump_to='permanames')
    dataset_versions = ma.Nested(DatasetVersionSummarySchema,
                                 many=True,
                                 dump_to='versions')
    parents = ma.Nested(FolderNamedIdSchema, dump_to='folders', many=True)


class DataFileSummarySchema(ma.ModelSchema):
    class Meta:
        additional = ('name', 'type', 'short_summary')

    # TODO: Manage the other fields in the model/db too
    type = EnumField(DataFile.DataFileType)


class DataFileSchema(ma.ModelSchema):
    class Meta:
        additional = ('id', 'name', 's3_bucket',
                      's3_key', 'short_summary')

    type = EnumField(DataFile.DataFileType)
    # Allowed Conversion Type
    allowed_conversion_type = fields.fields.Function(lambda obj: get_allowed_conversion_type(obj.type),
                                                     dump_to="allowed_conversion_type")
    # description = fields.fields.Function(lambda obj: 'TODO')
    # content_summary = fields.fields.Function(lambda obj: 'TODO')
    provenance_nodes = ma.Nested(ProvenanceNodeSchema(), many=True)


class DatasetVersionSchema(ma.ModelSchema):
    class Meta:
        # WARNING: long_summary is pretty heavy. Don't include it here, but create your own schema
        additional = ('id', 'name', 'dataset_id',
                      'creation_date', 'creator', 'datafiles',
                      'description', 'version', 'parents')

    creator = ma.Nested(UserNamedIdSchema)
    datafiles = ma.Nested(DataFileSchema, many=True)
    # TODO: Consolidate the term between folders and parents
    parents = ma.Nested(FolderNamedIdSchema, dump_to='folders', many=True)


class DatasetVersionFullDatasetSchema(ma.ModelSchema):
    class Meta:
        additional = ('id', 'name', 'dataset',
                      'creation_date', 'creator', 'datafiles',
                      'description', 'version', 'parents')

    dataset = ma.Nested(DatasetSchema)
    creator = ma.Nested(UserNamedIdSchema)
    datafiles = ma.Nested(DataFileSummarySchema, many=True)
    # TODO: Consolidate the term between folders and parents
    parents = ma.Nested(FolderNamedIdSchema, dump_to='folders', many=True)


class DatasetVersionLightSchema(ma.ModelSchema):
    class Meta:
        additional = ('id', 'name', 'dataset_id',
                      'creation_date', 'creator',
                      'description', 'version')

    creator = ma.Nested(UserNamedIdSchema)
    # datafiles = ma.Nested(DataFileSummarySchema, many=True)
    # TODO: Consolidate the term between folders and parents
    # parents = ma.Nested(FolderNamedIdSchema, dump_to='folders', many=True)


class DatasetFullSchema(ma.ModelSchema):
    # TODO: Change the name to DatasetWithVersionSchema, because we skip a few fields
    class Meta:
        additional = ('id', 'name', 'description',
                      'permaname', 'dataset_versions')

    # TODO: Change this field to properly handle multiple permanames (a new permaname is added when we change the name of the dataset)
    permaname = fields.fields.Function(lambda obj: [obj.permaname], dump_to='permanames')
    dataset_versions = ma.Nested(DatasetVersionLightSchema(),
                                 many=True,
                                 dump_to='versions')
    # parents = ma.Nested(FolderNamedIdSchema(), dump_to='folders', many=True)


class AccessLogSchema(ma.ModelSchema):
    class Meta:
        additional = ('user_id', 'entry', 'last_access')

    entry = ma.Nested(EntrySummarySchema)
