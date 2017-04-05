from flask_marshmallow import Marshmallow, fields
from marshmallow_enum import EnumField
from marshmallow_oneofschema import OneOfSchema

from taiga2.models import User, Folder, Entry, Dataset, DatasetVersion, DataFile

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


class DatasetSummarySchema(ma.ModelSchema):
    class Meta:
        additional = ('id', 'permaname')
    permaname = fields.fields.Function(lambda obj: [obj.permaname], dump_to='permanames')


class DatasetVersionSummarySchema(ma.ModelSchema):
    # TODO: Add status later
    class Meta:
        fields = ('id', 'name')


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
        model = DataFile
    type = EnumField(DataFile.DataFileType)
    description = fields.fields.Function(lambda obj: 'TODO')
    content_summary = fields.fields.Function(lambda obj: 'TODO')


class DatasetVersionSchema(ma.ModelSchema):
    class Meta:
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
