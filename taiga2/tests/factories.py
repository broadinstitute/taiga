import factory
from taiga2.tests.conftest import db
from taiga2.models import Group


class GroupFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Group
        sqlalchemy_session = db.session

    name = factory.Sequence(lambda n: "Group {}".format(n))