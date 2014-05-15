import csv
import sqlmeta
from injector import inject
import numpy as np
import h5py
import math
import json
import hashlib
import os
import subprocess
import tempfile
import taiga.columnar

def to_string_with_nan_mask(x):
  if math.isnan(x):
    return "NA"
  else:
    return str(x)

r_escape_str = lambda x: '"'+x.replace("\"", "\\\"")+'"'

class ConvertService(object):
  @inject(hdf5fs=sqlmeta.Hdf5Store)
  def __init__(self, hdf5fs):
    self.hdf5fs = hdf5fs
    self.str_dt = h5py.special_dtype(vlen=bytes)
  
  def hdf5_to_Rdata(self, hdf5_path, destination_file):
    # two step conversion: First convert to csv, then use R to load CSV and write Rdata file
    # a better strategy would be to use R's require(rhdf5) package to write without the intermediary file
    with tempfile.NamedTemporaryFile() as t:
      temp_path = t.name

      self.hdf5_to_tabular_csv(hdf5_path, temp_path)
      handle = subprocess.Popen(["R", "--vanilla"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      stdout, stderr = handle.communicate("data <- read.table(%s,sep=',',head=T,row.names=1); save(data, file=%s)" % (r_escape_str(temp_path), r_escape_str(destination_file)))
      if handle.returncode != 0:
        raise Exception("R process failed: %s\n%s" % (stdout, stderr))
  
  def Rdata_to_hdf5(self, input_path, dataset_id, hdf5_path, col_axis, row_axis):
    # two step conversion: First use R to convert to csv, then convert to HDF5
    with tempfile.NamedTemporaryFile() as t:
      temp_path = t.name

      handle = subprocess.Popen(["R", "--vanilla"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      stdout, stderr = handle.communicate("local.env <- new.env(); load(file=%s, local.env); write.table(local.env$data, file=%s, sep=',')" % (r_escape_str(input_path), r_escape_str(temp_path)))
      if handle.returncode != 0:
        raise Exception("R process failed: %s\n%s" % (stdout, stderr))

      self.tcsv_to_hdf5(temp_path, dataset_id, hdf5_path, col_axis, row_axis)
  
  def hdf5_to_gct(self, hdf5_path, destination_file):
    with self.hdf5fs.hdf5_open(hdf5_path) as f:
      with open(destination_file, "w") as fd_out:
        w = csv.writer(fd_out, delimiter="\t")

        data = f['data']

        row_header = f['dim_0']
        col_header = list(f['dim_1'])
        if 'gct_description' in f:
          descriptions = f['gct_description']
        else:
          descriptions = row_header

        w.writerow(["#1.2"])
        w.writerow([str(len(row_header)), str(len(col_header))])
        w.writerow(["Name", "Description"]+col_header)

        row_count = row_header.shape[0]
        for i in xrange(row_count):
          row = data[i,:]
          w.writerow([row_header[i], descriptions[i]] + [to_string_with_nan_mask(x) for x in row])

  def gct_to_hdf5(self, input_path, dataset_id, hdf5_path, col_axis, row_axis):
    # TODO: Reduce memory footprint of this conversion
    with open(input_path) as fd:
      version = fd.readline()
      assert version.strip() == "#1.2"
      r = csv.reader(fd, delimiter="\t")
      
      header_count_row = r.next()
      row_count = int(header_count_row[0])
      col_count = int(header_count_row[1])
      
      gct_header = r.next()
      
      col_header = gct_header[2:]
      names = []
      descriptions = []
      
      data_rows = []
      for row in r:
        names.append(row[0])
        descriptions.append(row[1])
        data_rows.append(row[2:])
    
      assert len(data_rows) == row_count
      assert len(data_rows[0]) == col_count
      
    data = np.empty((row_count, col_count),'d')
    data[:] = np.nan
    for row_i, row in enumerate(data_rows):
      for col_i, value in enumerate(row):
        if value == "NA" or value == '':
          parsed_value = np.nan
        else:
          parsed_value = float(value)
        data[row_i, col_i] = parsed_value

    with self.hdf5fs.hdf5_open(hdf5_path, mode="w") as f:
      self.write_hdf5_matrix(f, dataset_id, data, row_axis, names, col_axis, col_header)
      
      gct_description = f.create_dataset("gct_description", (len(descriptions),), dtype=self.str_dt)
      gct_description[:] = descriptions
  
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
    
      w.writerow([""]+list(col_header))
      row_count = row_header.shape[0]
      for i in xrange(row_count):
        row = data[i,:]
        w.writerow([row_header[i]] + [to_string_with_nan_mask(x) for x in row])
      fd_out.close()

  def tcsv_to_hdf5(self, input_path, dataset_id, hdf5_path, col_axis, row_axis):
    # TODO: Reduce memory footprint of this conversion
    with open(input_path) as fd:
      r = csv.reader(fd)
      col_header = r.next()
      row_header = []
      rows = []
      for row in r:
        row_header.append(row[0])
        rows.append(row[1:])
    
    # check to see, does the header line up with the number of columns in the row, or do we need to shift it by one?
    if col_header[0] == '':
      col_header=col_header[1:]
    
    data = np.empty((len(rows), len(rows[0])),'d')
    data[:] = np.nan
    for row_i, row in enumerate(rows):
      for col_i, value in enumerate(row):
        if value == "NA" or value == "":
          parsed_value = np.nan
        else:
          parsed_value = float(value)
        data[row_i, col_i] = parsed_value

    with self.hdf5fs.hdf5_open(hdf5_path, mode="w") as f:
      self.write_hdf5_matrix(f, dataset_id, data, row_axis, row_header, col_axis, col_header)

  def write_hdf5_matrix(self, f, dataset_id, data, row_axis, row_header, col_axis, col_header):
    f['data'] = data
    f['data'].attrs['id'] = dataset_id

    dim_0 = f.create_dataset("dim_0", (len(row_header),), dtype=self.str_dt)
    dim_0[:] = row_header
    dim_0.attrs['name'] = row_axis

    dim_1 = f.create_dataset("dim_1", (len(col_header),), dtype=self.str_dt)
    dim_1[:] = col_header
    dim_1.attrs['name'] = col_axis
    
  def tcsv_to_columnar(self, input_file, output_file, delimiter):
    taiga.columnar.convert_csv_to_tabular(input_file, output_file, delimiter)

  def columnar_to_tcsv(self, input_file, output_file, delimiter):
    taiga.columnar.convert_tabular_to_csv(input_file, output_file, delimiter)

  def columnar_to_Rdata(self, input_file, destination_file):
    # two step conversion: First convert to csv, then use R to load CSV and write Rdata file.  Not clear that we can do better 
    # at the moment
    with tempfile.NamedTemporaryFile() as t:
      temp_path = t.name

      self.columnar_to_tcsv(input_file, temp_path, ",")
      handle = subprocess.Popen(["R", "--vanilla"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      stdout, stderr = handle.communicate("data <- read.table(%s, sep=',', head=T, as.is=T); save(data, file=%s)" % (r_escape_str(temp_path), r_escape_str(destination_file)))
      if handle.returncode != 0:
        raise Exception("R process failed: %s\n%s" % (stdout, stderr))

class CacheFileHandle(object):
  """ Handle to a cached file.  Only self.name and self.done should be accessed """
  def __init__(self, filename, final_filename, needs_content):
    self.partial_filename = filename
    self.final_filename = final_filename
    self.needs_content = needs_content
    if self.needs_content:
      self.name = self.partial_filename
    else:
      self.name = self.final_filename
    
  def done(self):
    os.rename(self.partial_filename, self.final_filename)
    self.name = self.final_filename

class CacheService(object):
  """ Trivial caching service.  Relies on the filesystem and hashes of parameters.  Likely prone to race conditions which may not be important in low throughput situations """
  def __init__(self, temp_dir):
    self.temp_dir = os.path.abspath(temp_dir)
    if not os.path.exists(temp_dir):
      os.makedirs(temp_dir)
    
  def create_file_for(self, parameters):
    parameter_str = json.dumps(parameters, sort_keys=True)
    digest = hashlib.md5(parameter_str).hexdigest()
    
    metadata_file = "%s/temp-%s.json" % (self.temp_dir, digest)
    partial_file = tempfile.NamedTemporaryFile(dir=self.temp_dir, prefix="part-", delete=False).name
    final_file = "%s/final-%s.data" % (self.temp_dir, digest)
    
    if os.path.exists(metadata_file):
      with open(metadata_file) as fd:
        metadata_body = fd.read()
      assert metadata_body == parameter_str
    else:
      with open(metadata_file, "w") as fd:
        fd.write(parameter_str)
    
    if os.path.exists(final_file):
      return CacheFileHandle(None, final_file, False)
    else:
      return CacheFileHandle(partial_file, final_file, True)
