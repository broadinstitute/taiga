# triple
# subject predicate object -> stmt
# ref | str -> object 
# ref -> subject
# ref -> predicate

import sqlite3
import os
from collections import namedtuple
import uuid
import numpy as np
import h5py
import time
from contextlib import contextmanager
import math
import datetime
import time

from sqlalchemy import create_engine
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, DateTime, Boolean

DatasetSummary = namedtuple("DatasetSummary", [
  "id", 
  "name", 
  "created_timestamp", 
  "description", 
  "dataset_id", "created_by", "hdf5_path", 
  "version", "is_published", "data_type"])

# named_data(named_data_id, name, latest_version)
# data_version(data_id, named_data_id, version_id, description, created_date, created_by_user_id)
# owner = (user_id, name, email, api_token)
#lastrowid

#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///build/v2.sqlite3'

metadata = MetaData()

named_data = Table('named_data', metadata,
     Column('named_data_id', Integer, primary_key=True),
     Column('name', String),
     Column('latest_version', Integer),
)

data_version = Table('data_version', metadata,
     Column('dataset_id', String, primary_key=True),
     Column('named_data_id', None, ForeignKey('named_data.named_data_id')),
     Column('version', Integer),
     Column('description', String),
     Column('created_by_user_id', None, ForeignKey('user.user_id')),
     Column('created_timestamp', DateTime),
     Column('hdf5_path', String),
     Column('is_published', Boolean),
     Column('data_type', String)
)

user = Table('user', metadata, 
     Column('user_id', Integer, primary_key=True),
     Column('name', String),
     Column('email', String),
     Column('openid', String)
)

statement = Table("statement", metadata,
        Column("statement_id", Integer, primary_key=True),
        Column('subject', String, nullable=False),
        Column('predicate', String, nullable=False),
        Column('object_type', Integer, nullable=False),
        Column('object', String, nullable=False)
)


Ref = namedtuple("Ref", ["id"])

LITERAL_TYPE=1
REF_TYPE=2

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

class MetaStore(object):
  def __init__(self, filename):
    new_db = not os.path.exists(filename)
    self.engine = create_engine('sqlite:///%s' % filename, echo=True)
    if new_db:
      metadata.create_all(self.engine)

  def get_dataset_versions(self, dataset_name):
    with self.engine.begin() as db:
      result = db.execute("select v.dataset_id from named_data n join data_version v on n.named_data_id = v.named_data_id where n.name = ? order by v.version", (dataset_name,))
      return [self.get_dataset_by_id(x[0]) for x in result.fetchall()]

  def update_tags(self, dataset_id, tags):
    for s, p, o in self.find_stmt(Ref(dataset_id), Ref("hasTag"), None):
      self.delete_stmt(s, p, o)
    for tag in tags:
      self.insert_stmt(Ref(dataset_id), Ref("hasTag"), tag)
  
  def get_all_tags(self):
    return set([o for s, p, o in self.find_stmt(None, Ref("hasTag"), None)])
  
  def get_by_tag(self, tag):
    dataset_ids = set([s for s, p, o in self.find_stmt(None, Ref("hasTag"), tag)])
    return [self.get_dataset_by_id(dsid) for dsid in dataset_ids]
  
  def get_dataset_tags(self, dataset_id):
    return set([o for s, p, o in self.find_stmt(Ref(dataset_id), Ref("hasTag"), None)])
  
  def update_description(self, dataset_id, description):
    with self.engine.begin() as db:
      updated = db.execute("update data_version set description = ? where dataset_id = ?", (description, dataset_id))
    
  def get_dataset_by_id(self, dataset_id):
    with self.engine.begin() as db:
      row = db.execute("select v.dataset_id, n.name, v.created_timestamp, v.description, v.dataset_id, u.name, v.hdf5_path, v.version, v.is_published, v.data_type from named_data n join data_version v on n.named_data_id = v.named_data_id left join user u on u.user_id = v.created_by_user_id where v.dataset_id = ?", [dataset_id]).first()
      if row == None:
        return None
      # convert created_timestamp to a string
      row = list(row)
      #row[2] = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime(row[2]))
      return DatasetSummary(*row)
  
  def get_dataset_id_by_name(self, dataset_name, version=None):
    with self.engine.begin() as db:
      query = "select v.dataset_id from named_data n join data_version v on n.named_data_id = v.named_data_id WHERE n.name = ? "
      params = [dataset_name]
      if version == None or version == '':
        query += "AND n.latest_version = v.version"
      else:
        query += "AND v.version = ?"
        params.append(version)
      
      row = db.execute(query, params).first()
      if row == None:
        return None
      else:
        return row[0]

  def list_names(self):
    with self.engine.begin() as db:
      result = db.execute("select v.dataset_id from named_data n join data_version v on n.named_data_id = v.named_data_id AND n.latest_version = v.version")
      return [self.get_dataset_by_id(x[0]) for x in result.fetchall()]

  def register_dataset(self, name, dataset_id, is_published, data_type, description, created_by_user_id, hdf5_path, name_exists=False):
    print "register ", name, dataset_id, is_published, data_type, description, created_by_user_id, hdf5_path
    with self.engine.begin() as db:
      if not name_exists:
        next_version = 1
        named_data_id = db.execute(named_data.insert().values(name=name, latest_version=next_version)).inserted_primary_key[0]
      else:
        named_data_id = db.execute("select named_data_id from named_data where name = ?", [name]).first()[0]
        max_version = db.execute("select max(version) from data_version where named_data_id = ?", [named_data_id]).first()[0]
        next_version = max_version + 1
      
      db.execute(data_version.insert().values(dataset_id=dataset_id,
        named_data_id=named_data_id, 
        version=next_version, 
        description=description, 
        created_by_user_id=created_by_user_id, 
        created_timestamp=datetime.datetime.now(), 
        hdf5_path=hdf5_path,
        data_type=data_type,
        is_published=is_published))

      if next_version != 1:
        db.execute("update named_data set latest_version = ? where named_data_id = ?", [next_version, named_data_id])

  def insert_stmt(self, subject, predicate, object):
    object_type, object_str = prefix_object(object)
    with self.engine.begin() as db:
      db.execute("insert into statement (subject, predicate, object_type, object) values (?, ?, ?, ?)", (subject.id, predicate.id, object_type, object_str))
    
  def delete_stmt(self, subject, predicate, object):
    object_type, object_str = prefix_object(object)
    with self.engine.begin() as db:
      db.execute("delete from statement where subject = ? and predicate = ? and object = ? and object_type = ?", (subject.id, predicate.id, object_str, object_type))

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
      return [ (Ref(s), Ref(p), unprefix_object(o,ot)) for s, p, ot, o in result.fetchall() ]

  def exec_stmt_query(self, query):
    """ query is a list of statements, where each element in the triple is a dict {"id": ...} for references, 
      a dict {"var": ...} for a variable, or a literal.  Will return a list of dicts with assignments for each variable
    """
    return exec_sub_stmt_query(query, self.find_stmt, {})

  def get_user_details(self, openid):
    with self.engine.begin() as db:
      result = db.execute("select user_id, name, email from user where openid = ?", [openid])
      return result.fetchone()

  def persist_user_details(self, openid, email='', name=''):
    with self.engine.begin() as db:
      result = db.execute("select user_id from user where openid = ?", [openid])
      user_id = result.fetchone()
      if user_id == None:
        user_id = db.execute(user.insert().values(name=name, email=email, openid=openid)).inserted_primary_key[0]
  
  def find_all_data_types(self):
    with self.engine.begin() as db:
      result = db.execute("select distinct data_type from data_version")
      return [x[0] for x in result.fetchall()]
  
  def close(self):
    #self.engine.close()
    pass

@contextmanager
def open_hdf5_ctx_mgr(hdf5_path, mode="r"):
  f = h5py.File(hdf5_path, mode)
  yield f
  f.close()

Dimension = namedtuple("Dimension", ["name", "values"])

class Hdf5Store(object):
  def __init__(self, hdf5_root):
    self.hdf5_root = hdf5_root

  def create_new_dataset_id(self):
    dataset_id = str(uuid.uuid4())
    # TODO: make staggered dirs
    return (dataset_id, dataset_id+".hdf5")

  def get_dimensions(self, hdf5_path):
    with self.hdf5_open(hdf5_path) as f:
      attrs = list(f['data'].attrs.items())
      shape = f['data'].shape

      dims=[]
      for i in range(len(shape)):
        dim_vector = f['dim_%d' % i]
        dims.append( Dimension( name = dim_vector.attrs["name"], values = tuple(dim_vector)))
    
    return dims
  
  def hdf5_open(self, hdf5_path, mode="r"):
    hdf5_path = os.path.join(self.hdf5_root, hdf5_path)
    print "opening %s" % hdf5_path
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
  for i,x in enumerate(first_stmt):
    if type(x) == dict:
      if "id" in x:
        x=Ref(x['id'])
      elif "var" in x:
        vars_to_assign.append( (i, x['var']) )
        x=None
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

