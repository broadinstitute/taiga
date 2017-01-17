from flask_marshmallow import Marshmallow, fields
from marshmallow_enum import EnumField

from taiga2.models import User, Folder, Entry

ma = Marshmallow()


class UserSchema(ma.ModelSchema):
    class Meta:
        model = User


class UserNamedIdSchema(ma.ModelSchema):
    class Meta:
        fields = ('id', 'name')


class EntrySchema(ma.ModelSchema):
    # TODO: We need to rethink this because Entry is not (yet?) aware about all these attributes
    # TODO: A dataset does not have a creator because the dataset version has...should we print the creator of the last datasetVersion?
    class Meta:
        fields = ('type', 'id', 'name', 'creation_date',
                  'creator')
    creator = ma.Nested(UserNamedIdSchema)


class FolderSchema(ma.ModelSchema):
    class Meta:
        # We just don't take the folder_type because of the Enum
        fields = ('id', 'name', 'type', 'description',
                  'entries', 'creator', 'creation_date',
                  'folder_type')
    entries = ma.Nested(EntrySchema, many=True)
    creator = ma.Nested(UserNamedIdSchema)
    folder_type = EnumField(Folder.FolderType)


