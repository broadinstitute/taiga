# triple
# subject predicate object -> stmt
# ref | str -> object 
# ref -> subject
# ref -> predicate

import os
from collections import namedtuple
import uuid
import h5py
from contextlib import contextmanager
import datetime
import re
import random
import base64
from sqlalchemy import create_engine
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, DateTime, Boolean, UniqueConstraint
import sqlalchemy as sa
import sqlite3

DatasetSummary = namedtuple("DatasetSummary", [
    "id",
    "name",
    "created_timestamp",
    "description",
    "dataset_id",
    "created_by",
    "hdf5_path",
    "columnar_path",
    "version", "is_published", "data_type", "permaname", "is_public"])

# named_data(named_data_id, name, latest_version)
# data_version(data_id, named_data_id, version_id, description, created_date, created_by_user_id)
# owner = (user_id, name, email, api_token)
# lastrowid

# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///build/v2.sqlite3'

metadata = MetaData()

view_history = Table('view_history', metadata,
                     Column('view_history_id', sa.Integer, primary_key=True),
                     Column('user_id', sa.Integer, sa.ForeignKey('user.user_id')),
                     Column('dataset_id', String),
                     Column('latest_view', DateTime),
                     Column('view_count', sa.Integer),
                     sa.UniqueConstraint('user_id', 'dataset_id', name='uk_view_history'),
                     sqlite_autoincrement=True
                     )

named_data = Table('named_data', metadata,
                   sa.Column('named_data_id', sa.Integer, primary_key=True),
                   sa.Column('name', sa.String),
                   sa.Column('permaname', sa.String),
                   sa.Column('latest_version', sa.Integer),
                   sa.Column('is_public', sa.Boolean),
                   sa.UniqueConstraint('name', name='uk_named_data_name'),
                   sa.UniqueConstraint('permaname', name='uk_perma_named_name')
                   )

named_data_user = Table('named_data_user', metadata,
                        sa.Column('id', sa.Integer, primary_key=True),
                        sa.Column('named_data_id', sa.Integer, sa.ForeignKey('named_data.named_data_id')),
                        sa.Column('user_id', sa.Integer, sa.ForeignKey('user.user_id')),
                        sa.UniqueConstraint('named_data_id', "user_id", name='uk_named_data_user'),
                        )

data_version = Table('data_version', metadata,
                     Column('dataset_id', String, primary_key=True),
                     Column('named_data_id', None, ForeignKey('named_data.named_data_id')),
                     Column('version', Integer),
                     Column('description', String),
                     Column('created_by_user_id', None, ForeignKey('user.user_id')),
                     Column('created_timestamp', DateTime),
                     Column('hdf5_path', String),
                     Column('columnar_path', String),
                     Column('is_published', Boolean),
                     Column('data_type', String),
                     Column('is_deprecated', Boolean),
                     Column('uploaded_md5', String),
                     Column('downloaded_count', Integer)
                     )

user = Table('user', metadata,
             Column('user_id', Integer, primary_key=True),
             Column('name', String),
             Column('email', String),
             Column('openid', String),
             Column('token', String)
             )

statement = Table("statement", metadata,
                  Column("statement_id", Integer, primary_key=True),
                  Column('subject', String, nullable=False),
                  Column('predicate', String, nullable=False),
                  Column('object_type', Integer, nullable=False),
                  Column('object', String, nullable=False)
                  )

named_data_tag = Table('named_data_tag', metadata,
                       Column('named_data_tag_id', Integer, primary_key=True),
                       Column('named_data_id', Integer, ForeignKey('named_data.named_data_id'), nullable=False),
                       Column('tag', String, nullable=False), sqlite_autoincrement=True
                       )

Ref = namedtuple("Ref", ["id"])

LITERAL_TYPE = 1
REF_TYPE = 2


def prefix_object(object):
    if isinstance(object, Ref):
        return REF_TYPE, object.id
    else:
        return LITERAL_TYPE, object


def unprefix_object(object_str, object_type):
    if object_type == REF_TYPE:
        return Ref(object_str)
    elif object_type == LITERAL_TYPE:
        return object_str
    else:
        raise Exception("invalid type %d" % object_type)


def create_permaname(name, permaname_exists_callback):
    permaname = re.sub("['\"]+", "", name.lower())
    permaname = re.sub("[^A-Za-z0-9]+", "-", permaname)
    if permaname_exists_callback(permaname):
        suffix = 1
        while True:
            suffixed = "%s-%s" % (permaname, suffix)
            if not permaname_exists_callback(suffixed):
                break
            suffix += 1
        permaname = suffixed
    return permaname


def exec_insert_update_uk(db, insert_stmt, update_stmt=None):
    try:
        db.execute(insert_stmt)
    except sqlite3.IntegrityError:
        if update_stmt is not None:
            db.execute(update_stmt)
    except sa.exc.IntegrityError:
        if update_stmt is not None:
            db.execute(update_stmt)
    except:
        import sys
        type, value, traceback = sys.exc_info()
        print "type=%s %s" % (type, repr(type))
        print "typefile=%s" % (type.__file__,)
        raise


class MetaStore(object):
    def __init__(self, filename, metadata_log_filename):
        new_db = not os.path.exists(filename)
        self.engine = create_engine('sqlite:///%s' % filename, echo=True)
        if new_db:
            metadata.create_all(self.engine)
        self.metadata_log_filename = metadata_log_filename

    def create_new_dataset_id(self, suffix):
        dataset_id = str(uuid.uuid4())
        # TODO: make staggered dirs
        return (dataset_id, dataset_id + suffix)

    def _log_metadata_op(self, message, *args):
        with open(self.metadata_log_filename, "a") as fd:
            msg_with_args = datetime.datetime.now().isoformat() + " " + message + ": " + (
            " ".join([repr(x) for x in args])) + "\n"
            fd.write(msg_with_args)

    def get_dataset_versions(self, dataset_name):
        with self.engine.begin() as db:
            def fetch(condition):
                return db.execute(
                    "select v.dataset_id from named_data n join data_version v on n.named_data_id = v.named_data_id where " + condition + " order by v.version",
                    (dataset_name,)).fetchall()

            # first try permaname.  If that fails, fall back to the legacy behavior of searching by name
            result = fetch("n.permaname = ?")
            if len(result) == 0:
                result = fetch("n.name = ?")
            return [self.get_dataset_by_id(x[0]) for x in result]

    def get_named_data_id(self, db, dataset_id):
        return db.execute("select named_data_id from data_version where dataset_id = ?", [dataset_id]).fetchone()[0]

    def update_tags(self, dataset_id, tags):
        with self.engine.begin() as db:
            named_data_id = self.get_named_data_id(db, dataset_id)
            db.execute("delete from named_data_tag where named_data_id = ?", [named_data_id])
            for tag in tags:
                db.execute(named_data_tag.insert().values(named_data_id=named_data_id,
                                                          tag=tag))
            self._log_metadata_op("update_tags", dataset_id, tags)

    def get_all_tags(self):
        with self.engine.begin() as db:
            rows = db.execute("select tag, count(1) from named_data_tag group by tag").fetchall()
            return rows

    def get_by_tag(self, tag, user_id):
        with self.engine.begin() as db:
            rows = db.execute(
                "select dv.dataset_id from named_data_tag ndt join named_data nd on nd.named_data_id = ndt.named_data_id join data_version dv on (dv.named_data_id = ndt.named_data_id and dv.version = nd.latest_version) where tag = ? and (nd.is_public = ? or exists (select 1 from named_data_user ndu where ndu.named_data_id = nd.named_data_id and user_id = ?))",
                [tag, True, user_id]).fetchall()
            return [self.get_dataset_by_id(x[0]) for x in rows]

    def get_dataset_tags(self, dataset_id):
        with self.engine.begin() as db:
            rows = db.execute(
                "select ndt.tag from named_data_tag ndt join data_version dv on dv.named_data_id = ndt.named_data_id where dv.dataset_id = ?",
                [dataset_id]).fetchall()
            return [x[0] for x in rows]

    def update_dataset_name(self, dataset_id, name):
        with self.engine.begin() as db:
            named_data_id = self.get_named_data_id(db, dataset_id)
            db.execute("update named_data set name = ? where named_data_id = ?", [name, named_data_id])
            self._log_metadata_op("update_dataset_name", dataset_id, name)

    def update_dataset_field(self, dataset_id, field_name, value):
        if field_name == "is_public":
            with self.engine.begin() as db:
                updated = db.execute(
                    "update named_data set " + field_name + " = ? where named_data_id = (select named_data_id from data_version where dataset_id = ?)",
                    (value, dataset_id))
                self._log_metadata_op("update_dataset_field", dataset_id, field_name, value)
        else:
            assert field_name in ("description", "data_type", "is_published")
            with self.engine.begin() as db:
                updated = db.execute("update data_version set " + field_name + " = ? where dataset_id = ?",
                                     (value, dataset_id))
                self._log_metadata_op("update_dataset_field", dataset_id, field_name, value)

    def get_dataset_by_id(self, dataset_id):
        with self.engine.begin() as db:
            row = db.execute(
                "select v.dataset_id, n.name, v.created_timestamp, v.description, v.dataset_id, u.name, v.hdf5_path, v.columnar_path, v.version, v.is_published, v.data_type, n.permaname, n.is_public from named_data n join data_version v on n.named_data_id = v.named_data_id left join user u on u.user_id = v.created_by_user_id where v.dataset_id = ?",
                [dataset_id]).first()
            if row == None:
                return None
            # convert created_timestamp to a string
            row = list(row)
            # row[2] = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime(row[2]))
            return DatasetSummary(*row)

    def get_dataset_id_by_name(self, dataset_name, version=None):
        with self.engine.begin() as db:
            def fetch(condition):
                query = "select v.dataset_id from named_data n join data_version v on n.named_data_id = v.named_data_id WHERE " + condition
                params = [dataset_name]
                if version == None or version == '':
                    query += "AND n.latest_version = v.version"
                else:
                    query += "AND v.version = ?"
                    params.append(version)
                return db.execute(query, params).first()

            # first try permaname, and fall back to searching name if nothing found
            row = fetch("n.permaname = ?")
            if row == None:
                row = fetch("n.name = ?")

            if row == None:
                return None
            else:
                return row[0]

    def find_by_md5(self, permaname, md5):
        with self.engine.begin() as db:
            result = db.execute(
                "select v.dataset_id from named_data n join data_version v on n.named_data_id = v.named_data_id where v.uploaded_md5 = ? and n.permaname = ? order by v.version desc",
                [md5, permaname])
            row = result.first()
            if row == None:
                return None
            else:
                return row[0]

    def list_names(self, user_id):
        with self.engine.begin() as db:
            result = db.execute(
                "select v.dataset_id from named_data n join data_version v on n.named_data_id = v.named_data_id AND n.latest_version = v.version and (n.is_public = ? or exists (select 1 from named_data_user ndu where ndu.named_data_id = n.named_data_id and user_id = ?))",
                [True, user_id])
            return [self.get_dataset_by_id(x[0]) for x in result.fetchall()]

    def _find_next_version(self, db, name_exists, name, is_public, owner_id, permaname):
        if not name_exists:
            next_version = 1

            def _permaname_exists(name):
                exists = len(
                    db.execute("select named_data_id from named_data where permaname = ?", [name]).fetchall()) > 0
                return exists

            if permaname is None:
                permaname = create_permaname(name, _permaname_exists)
            named_data_id = db.execute(
                named_data.insert().values(name=name, permaname=permaname, latest_version=next_version,
                                           is_public=is_public)).inserted_primary_key[0]
            if not is_public:
                db.execute(named_data_user.insert().values(named_data_id=named_data_id, user_id=owner_id))
        else:
            named_data_id = db.execute("select named_data_id from named_data where name = ?", [name]).first()[0]
            max_version = \
            db.execute("select max(version) from data_version where named_data_id = ?", [named_data_id]).first()[0]
            next_version = max_version + 1
        return next_version, named_data_id

    def _update_next_version(self, db, next_version, named_data_id):
        if next_version != 1:
            db.execute("update named_data set latest_version = ? where named_data_id = ?",
                       [next_version, named_data_id])

    def register_dataset(self, name, dataset_id, is_published, data_type, description, created_by_user_id, hdf5_path,
                         is_public, name_exists=False, permaname=None, uploaded_md5=None):
        with self.engine.begin() as db:
            next_version, named_data_id = self._find_next_version(db, name_exists, name, is_public, created_by_user_id,
                                                                  permaname)

            db.execute(data_version.insert().values(dataset_id=dataset_id,
                                                    named_data_id=named_data_id,
                                                    version=next_version,
                                                    description=description,
                                                    created_by_user_id=created_by_user_id,
                                                    created_timestamp=datetime.datetime.now(),
                                                    hdf5_path=hdf5_path,
                                                    data_type=data_type,
                                                    is_published=is_published,
                                                    is_deprecated=False,
                                                    downloaded_count=0,
                                                    uploaded_md5=uploaded_md5))

            self._update_next_version(db, next_version, named_data_id)
            self._log_metadata_op("register_dataset", name, dataset_id, is_published, data_type, description,
                                  created_by_user_id, hdf5_path, is_published, name_exists)

    def register_columnar_dataset(self, name, dataset_id, is_published, description, created_by_user_id, columnar_path,
                                  is_public, name_exists, permaname=None, uploaded_md5=None):
        with self.engine.begin() as db:
            next_version, named_data_id = self._find_next_version(db, name_exists, name, is_public, created_by_user_id,
                                                                  permaname)

            db.execute(data_version.insert().values(dataset_id=dataset_id,
                                                    named_data_id=named_data_id,
                                                    version=next_version,
                                                    description=description,
                                                    created_by_user_id=created_by_user_id,
                                                    created_timestamp=datetime.datetime.now(),
                                                    columnar_path=columnar_path,
                                                    is_published=is_published,
                                                    is_deprecated=False,
                                                    downloaded_count=0,
                                                    uploaded_md5=uploaded_md5))

            self._update_next_version(db, next_version, named_data_id)
            self._log_metadata_op("register_columnar_dataset", name, dataset_id, is_published, description,
                                  created_by_user_id, columnar_path, is_public, name_exists)

    def record_view(self, user_id, dataset_id):
        print "record_view"
        with self.engine.begin() as db:
            now = datetime.datetime.now()
            named_data_id = db.execute(
                sa.select([data_version.c.named_data_id]).where(data_version.c.dataset_id == dataset_id)).first()[0]
            print "params", named_data_id, user_id
            exec_insert_update_uk(db, named_data_user.insert().values(named_data_id=named_data_id, user_id=user_id))
            rs = db.execute(view_history.update()
                            .where(view_history.c.dataset_id == dataset_id and view_history.c.user_id == user_id)
                            .values(view_count=view_history.c.view_count + 1, latest_view=now))
            if rs.rowcount == 0:
                db.execute(
                    view_history.insert().values(user_id=user_id, dataset_id=dataset_id, latest_view=now, view_count=1))

    def list_recent_views(self, user_id):
        with self.engine.begin() as db:
            dataset_ids = db.execute(
                sa.select([view_history.c.dataset_id]).where(view_history.c.user_id == user_id).order_by(
                    view_history.c.latest_view.desc())).fetchall()
            return [x[0] for x in dataset_ids]

    def insert_stmt(self, subject, predicate, object):
        object_type, object_str = prefix_object(object)
        with self.engine.begin() as db:
            db.execute("insert into statement (subject, predicate, object_type, object) values (?, ?, ?, ?)",
                       (subject.id, predicate.id, object_type, object_str))

    def delete_stmt(self, subject, predicate, object):
        object_type, object_str = prefix_object(object)
        with self.engine.begin() as db:
            db.execute("delete from statement where subject = ? and predicate = ? and object = ? and object_type = ?",
                       (subject.id, predicate.id, object_str, object_type))

    def find_stmt(self, subject, predicate, object):
        predicates = []
        parameters = []
        if subject != None:
            predicates.append("subject = ?")
            parameters.append(subject.id)
        if predicate != None:
            predicates.append("predicate = ?")
            parameters.append(predicate.id)
        if object != None:
            predicates.append("object_type = ? and object = ?")
            parameters.extend(prefix_object(object))

        query = "select subject, predicate, object_type, object from statement where %s" % (" AND ".join(predicates))
        with self.engine.begin() as db:
            result = db.execute(query, parameters)
            return [(Ref(s), Ref(p), unprefix_object(o, ot)) for s, p, ot, o in result.fetchall()]

    def exec_stmt_query(self, query):
        """ query is a list of statements, where each element in the triple is a dict {"id": ...} for references,
          a dict {"var": ...} for a variable, or a literal.  Will return a list of dicts with assignments for each variable
        """
        return exec_sub_stmt_query(query, self.find_stmt, {})

    def get_user_id_by_token(self, token):
        with self.engine.begin() as db:
            result = db.execute(sa.select([user.c.user_id]).where(user.c.token == token))
            return result.fetchone()

    def get_user_details(self, openid=None, user_id=None):
        with self.engine.begin() as db:
            if openid != None:
                result = db.execute("select user_id, name, email, token from user where openid = ?", [openid])
            else:
                result = db.execute("select user_id, name, email, token from user where user_id = ?", [user_id])
            return result.fetchone()

    def reset_user_token(self, user_id):
        with self.engine.begin() as db:
            new_token = base64.b64encode(bytes([random.randint(0, 255) for x in range(100)]))[:32]
            db.execute(user.update().values(token=new_token).where(user.c.user_id == user_id))

    def persist_user_details(self, openid, email='', name=''):
        with self.engine.begin() as db:
            result = db.execute("select user_id from user where openid = ?", [openid])
            user_id = result.fetchone()
            if user_id == None:
                user_id = db.execute(user.insert().values(name=name, email=email, openid=openid)).inserted_primary_key[
                    0]
            self._log_metadata_op("persist_user_details", openid, email, name)

    def find_all_data_types(self):
        with self.engine.begin() as db:
            result = db.execute("select distinct data_type from data_version where data_type is not null")
            return [x[0] for x in result.fetchall()]

    def close(self):
        # self.engine.close()
        pass


@contextmanager
def open_hdf5_ctx_mgr(hdf5_path, mode="r"):
    try:
        f = h5py.File(hdf5_path, mode)
    except IOError, e:
        raise IOError("Could not open %s" % hdf5_path, e)
    yield f
    f.close()


Dimension = namedtuple("Dimension", ["name", "value_count"])


class Hdf5Store(object):
    def __init__(self, hdf5_root):
        self.hdf5_root = hdf5_root

    def get_dimensions(self, hdf5_path):
        with self.hdf5_open(hdf5_path) as f:
            attrs = list(f['data'].attrs.items())
            shape = f['data'].shape

            dims = []
            for i in range(len(shape)):
                dim_vector = f['dim_%d' % i]
                dims.append(Dimension(name=dim_vector.attrs["name"], value_count=dim_vector.shape[0]))

        return dims

    def hdf5_open(self, hdf5_path, mode="r"):
        hdf5_path = os.path.join(self.hdf5_root, hdf5_path)
        return open_hdf5_ctx_mgr(hdf5_path, mode)


def exec_sub_stmt_query(query, find_stmt, bindings):
    """ query is a list of statements, where each element in the triple is a dict {"id": ...} for references,
        a dict {"var": ...} for a variable, or a literal.  Will return a list of dicts with assignments for each variable
    """
    if len(query) == 0:
        return [bindings]

    # for each call, we only worry about trying to satisfy a single statment
    first_stmt = query[0]
    masked_stmt = []
    vars_to_assign = []

    # convert statement into form with None for wildcard
    for i, x in enumerate(first_stmt):
        if type(x) == dict:
            if "id" in x:
                x = Ref(x['id'])
            elif "var" in x:
                vars_to_assign.append((i, x['var']))
                x = None
            else:
                raise Exception("malformed query: %s" % repr(query))
        else:
            x = str(x)

        masked_stmt.append(x)

    def assign(stmt, binding):
        result = []
        for x in stmt:
            if 'var' in x:
                name = x['var']
                if name in binding:
                    x = binding[name]
            result.append(x)
        return result

    rest = query[1:]
    stmts = find_stmt(*masked_stmt)

    # for each result, bind the value and save it into the list of results
    results = []
    for stmt in stmts:
        row = dict(bindings)
        for i, var_name in vars_to_assign:
            value = stmt[i]
            if isinstance(value, Ref):
                value = {"id": value.id}
            row[var_name] = value
        print "row=%s" % repr(row)
        rest_with_assignments = [assign(x, row) for x in rest]
        # recurse to satisfy remaining statements
        results.extend(exec_sub_stmt_query(rest_with_assignments, find_stmt, row))
    return results
