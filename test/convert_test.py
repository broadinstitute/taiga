import taiga.sqlmeta
import tempfile
import os
from nose import with_setup
from taiga.convert import ConvertService
import shutil

tempdir = None
cs = None

def setup():
  global tempdir
  global cs
  
  tempdir = tempfile.mkdtemp("convert-test")
  hdf5fs = taiga.sqlmeta.Hdf5Store(tempdir)
  cs = ConvertService(hdf5fs)

def cleanup_temp_file():
  if os.path.exists(tempdir):
    shutil.rmtree(tempdir)

GCT_CONTENTS = "\r\n".join([
  "#1.2", 
  "2\t2",
  "Name\tDescription\ta\tb",
  "c\tcdesc\t1.0\t2.0",
  "d\tddesc\t3.0\t4.0",
  ""])

GCT_NO_DESC_CONTENTS = "\r\n".join([
  "#1.2", 
  "2\t2",
  "Name\tDescription\ta\tb",
  "c\tc\t1.0\t2.0",
  "d\td\t3.0\t4.0",
  ""])


TCSV_CONTENTS = "\r\n".join([
  ",a,b",
  "c,1.0,2.0",
  "d,3.0,4.0",
  ""])

RSTYLE_TCSV_CONTENTS = "\r\n".join([
  "a,b",
  "c,1.0,2.0",
  "d,3.0,4.0",
  ""])
  
CSV_CONTENTS = "\r\n".join([
  "c,a,1.0",
  "d,a,3.0",
  "c,b,2.0",
  "d,b,4.0",
  ""
])

def write_tmp(text):
  fn = tempdir+"/source"
  with open(fn, "w") as fd:
    fd.write(text)
  return fn

def verify_file(filename, expected_content):
  content = open(filename).read()
  assert expected_content == content, "%s != %s" % (repr(expected_content), repr(content) )

@with_setup(setup, cleanup_temp_file)
def test_import_gct_export_gct():
  hdf5_path = tempdir+"/hdf5"
  final_file = tempdir+"/final"
  cs.gct_to_hdf5(write_tmp(GCT_CONTENTS), "dsid", hdf5_path, "col", "row")
  cs.hdf5_to_gct(hdf5_path, final_file)
  verify_file(final_file, GCT_CONTENTS)
  
@with_setup(setup, cleanup_temp_file)
def test_import_tcsv_export_gct():
  hdf5_path = tempdir+"/hdf5"
  final_file = tempdir+"/final"
  cs.tcsv_to_hdf5(write_tmp(TCSV_CONTENTS), "dsid", hdf5_path, "col", "row")
  cs.hdf5_to_gct(hdf5_path, final_file)
  verify_file(final_file, GCT_NO_DESC_CONTENTS)

@with_setup(setup, cleanup_temp_file)
def test_import_gct_export_tcsv():
  hdf5_path = tempdir+"/hdf5"
  final_file = tempdir+"/final"
  cs.gct_to_hdf5(write_tmp(GCT_CONTENTS), "dsid", hdf5_path, "col", "row")
  cs.hdf5_to_tabular_csv(hdf5_path, final_file, delimiter=",")
  verify_file(final_file, TCSV_CONTENTS)

@with_setup(setup, cleanup_temp_file)
def test_import_tcsv_export_tcsv():
  hdf5_path = tempdir+"/hdf5"
  final_file = tempdir+"/final"
  cs.tcsv_to_hdf5(write_tmp(TCSV_CONTENTS), "dsid", hdf5_path, "col", "row")
  cs.hdf5_to_tabular_csv(hdf5_path, final_file, delimiter=",")
  verify_file(final_file, TCSV_CONTENTS)

@with_setup(setup, cleanup_temp_file)
def test_import_rstyle_tcsv_export_tcsv():
  hdf5_path = tempdir+"/hdf5"
  final_file = tempdir+"/final"
  cs.tcsv_to_hdf5(write_tmp(RSTYLE_TCSV_CONTENTS), "dsid", hdf5_path, "col", "row")
  cs.hdf5_to_tabular_csv(hdf5_path, final_file, delimiter=",")
  verify_file(final_file, TCSV_CONTENTS)

@with_setup(setup, cleanup_temp_file)
def test_import_tcsv_export_csv():
  hdf5_path = tempdir+"/hdf5"
  final_file = tempdir+"/final"
  cs.tcsv_to_hdf5(write_tmp(TCSV_CONTENTS), "dsid", hdf5_path, "col", "row")
  cs.hdf5_to_csv(hdf5_path, final_file, delimiter=",")
  verify_file(final_file, CSV_CONTENTS)
