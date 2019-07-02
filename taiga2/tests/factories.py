import datetime

import factory

from taiga2.models import db as _db
from taiga2.models import Group, User, Folder, Entry
from taiga2.models import generate_uuid, generate_str_uuid


class UserFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session = _db.session

    id = factory.LazyFunction(generate_uuid)

    name = factory.Faker("name")

    email = factory.Faker("email")
    token = factory.LazyFunction(generate_str_uuid)

    # TODO: Home folder and Trash folder
    home_folder = factory.RelatedFactory("taiga2.tests.factories.FolderFactory")
    trash_folder = factory.RelatedFactory("taiga2.tests.factories.FolderFactory")


class GroupFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Group
        sqlalchemy_session = _db.session

    name = factory.Sequence(lambda n: "Group {}".format(n))

    users = factory.List([factory.SubFactory(UserFactory)])


class EntryFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Entry
        sqlalchemy_session = _db.session
        sqlalchemy_session_persistence = "flush"

    id = factory.LazyFunction(generate_uuid)
    name = factory.Faker("name")

    creation_date = factory.LazyFunction(datetime.datetime.utcnow)

    creator = factory.SubFactory(UserFactory)

    description = factory.Faker("text")


class FolderFactory(EntryFactory):
    class Meta:
        model = Folder
        sqlalchemy_session = _db.session

    type = Folder.__name__

    folder_type = Folder.FolderType.folder

    # TODO: Might be a problem here as we are giving a unique Entry instead of a list
    entries = factory.List([factory.SubFactory(EntryFactory)])
