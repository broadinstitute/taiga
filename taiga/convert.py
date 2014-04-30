import csv
import sqlmeta
from injector import inject
import numpy as np
import h5py
import math

def to_string_with_nan_mask(x):
  if math.isnan(x):
    return "NA"
  else:
    return str(x)

class ConvertService(object):
  @inject(hdf5fs=sqlmeta.Hdf5Store)
  def __init__(self, hdf5fs):
    self.hdf5fs = hdf5fs
  
  def hdf5_to_csv(self, hdf5_path, destination_file, delimiter=","):
    with self.hdf5fs.hdf5_open(hdf5_path) as f:
      fd_out = open(destination_file, "w")
      w = csv.writer(fd_out, delimiter=delimiter)

      data = f['data']

      row_header = f['dim_0']
      col_header = f['dim_1']

      row_count = row_header.shape[0]
      col_count = col_header.shape[0]
      for col_i in xrange(col_count):
        for row_i in xrange(row_count):
          element = data[row_i,col_i]
          if not math.isnan(element):
            w.writerow([row_header[row_i], col_header[col_i], element])
      fd_out.close()
    
  def hdf5_to_tabular_csv(self, hdf5_path, destination_file, delimiter=","):
    with self.hdf5fs.hdf5_open(hdf5_path) as f:
      fd_out = open(destination_file, "w")
      w = csv.writer(fd_out, delimiter=delimiter)

      data = f['data']

      row_header = f['dim_0']
      col_header = f['dim_1']
    
      w.writerow(col_header)
      row_count = row_header.shape[0]
      for i in xrange(row_count):
        row = data[i,:]
        w.writerow([row_header[i]] + [to_string_with_nan_mask(x) for x in row])
      fd_out.close()

  def convert_2d_csv_to_hdf5(self, input_file, col_axis, row_axis):
    dataset_id, hdf5_path = self.hdf5fs.create_new_dataset_id()
    
    # TODO: Reduce memory footprint of this conversion
    with open(input_file) as fd:
      r = csv.reader(fd)
      col_header = r.next()
      row_header = []
      rows = []
      for row in r:
        row_header.append(row[0])
        rows.append(row[1:])
    data = np.empty((len(rows), len(rows[0])),'d')
    data[:] = np.nan
    for row_i, row in enumerate(rows):
      for col_i, value in enumerate(row):
        if value == "NA":
          parsed_value = np.nan
        else:
          parsed_value = float(value)
        data[row_i, col_i] = parsed_value

    with self.hdf5fs.hdf5_open(hdf5_path, mode="w") as f:
      str_dt = h5py.special_dtype(vlen=bytes)

      f['data'] = data
      f['data'].attrs['id'] = dataset_id
  
      dim_0 = f.create_dataset("dim_0", (len(row_header),), dtype=str_dt)
      dim_0[:] = row_header
      dim_0.attrs['name'] = row_axis

      dim_1 = f.create_dataset("dim_1", (len(col_header),), dtype=str_dt)
      dim_1[:] = col_header
      dim_1.attrs['name'] = col_axis

    return (dataset_id, hdf5_path)



  