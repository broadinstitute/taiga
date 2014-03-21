# triple
# subject predicate object -> stmt
# ref | str -> object 
# ref -> subject
# ref -> predicate

import sqlite3
import os
from collections import namedtuple

DatasetSummary = namedtuple("DatasetSummary", ["id", "name", "created_timestamp", "description", "dataset_id", "created_by"])

# named_data(named_data_id, name, latest_version)
# data_version(data_id, named_data_id, version_id, description, created_date, created_by_user_id)
# owner = (user_id, name, email, api_token)
#lastrowid
class MetaDb:
  def __init__(self, filename):
    new_db = not os.path.exists(filename)
    self.connection = sqlite3.connect(filename)
    self.db = self.connection.cursor()
    if new_db:
      stmts = [
        "create table named_data (named_data_id integer primary key not null, name text, latest_version integer)",
        "create table data_version (data_id text primary key not null, named_data_id integer, version integer, description text, created_by_user_id integer, created_timestamp datetime)",
        "create table user (user_id integer primary key not null, name text, email text, api_token text)",
        "alter table data_version add constraint uk_data_version_1 unique (named_data_id, version)"
        ]
      for stmt in stmts:
        self.db.execute(stmt)

  def get_dataset_versions(self, dataset_name):
    raise
    
  def get_dataset_by_name(self, dataset_name, version=None):
    raise
    #self.db.execute("select v.data_id, n.name, v.created_timestamp, v.description, v.dataset_id, u.name from named_data n join data_version v on n.named_data_id = v.named_data_id join user u on u.user_id = v.created_by_user_id where ")
    #return DatasetSummary(*x) for x in self.db.fetch()

  def list_names(self):
    self.db.execute("select v.data_id, n.name, v.created_timestamp, v.description, v.dataset_id, u.name from named_data n join data_version v on n.named_data_id = v.named_data_id join user u on u.user_id = v.created_by_user_id")
    return [DatasetSummary(*x) for x in self.db.fetchall()]

  def register_dataset(self, name, dataset_id, description, created_by_user_id, hdf5_path, name_exists=False):
    if not name_exists:
      self.db.execute("insert into named_data (name, latest_version) values (?, 0)")
      named_data_id = db.lastrowid
      next_version = 0
    else:
      named_data_id = self.db.execute("select named_data_id from named_data where name = ?", [name])
      self.db.execute("select max(version) from named_data where named_data_id = ?", [named_data_id])
      next_version = self.fetch()[0] + 1
      
    self.db.execute("insert into data_version (data_id, named_data_id, version, description, created_by_user_id, created_timestamp, hdf5_path) values (?, ?, ?, ?, ?, ?, ?)", [dataset_id, named_data_id, next_version, description, created_by_user_id, hdf5_path])

    if next_version != 0:
      self.db.execute("update named_data set latest_version = ? where named_data_id = ?", [next_version, named_data_id])
      
    self.connection.commit()

  def close(self):
    self.cursor.close()
    self.connection.close()

class Hdf5FsDb:
  def __init__(self, metaDb, hdf5_root):
    self.hdf5_root = hdf5_root

  def create_new_dataset_id(self):
    dataset_id = str(uuid.uuid4())
    # TODO: make staggered dirs
    return (datset_id, os.path.join(self.hdf5_root, dataset_id+".hdf5"))

  def get_dimensions(self, hdf5_path):
    with self.hdf5_open(hdf5_path) as f:
      attrs = list(f['data'].attrs.items())
      shape = f['data'].shape

      dims=[]
      for i in range(len(shape)):
        dim_vector = f['dim_%d' % i]
        dims.append( Dimension( name = dim_vector.attrs["name"], values = tuple(dim_vector)))
    
    return dims

class ImportService:
  
  def convert_csv_to_hdf5(self, filename, col_axis, row_axis):
    # TODO: Reduce memory footprint of this conversion
    with open(filename) as fd:
      r = csv.reader(fd)
      col_header = r.next()
      row_header = []
      rows = []
      for row in r:
        row_header.append(row[0])
        rows.append(row[1:])
    data = np.zeros((len(rows), len(rows[0])),'f')
    for row_i, row in enumerate(rows):
      for col_i, value in enumerate(row):
        data[row_i, col_i] = value


    f = h5py.File(filename, "w")
    str_dt = h5py.special_dtype(vlen=bytes)

    f['data'] = data
    f['data'].attrs['id'] = dsid
  
    dim_0 = f.create_dataset("dim_0", (len(row_header),), dtype=str_dt)
    dim_0[:] = row_header
    dim_0.attrs['name'] = row_axis

    dim_1 = f.create_dataset("dim_1", (len(col_header),), dtype=str_dt)
    dim_1[:] = col_header
    dim_1.attrs['name'] = col_axis
    f.close()

    return filename

  