import taiga.columnar
from nose import with_setup
import tempfile
import shutil
import os
import csv

tempdir = None

def setup():
  global tempdir
  
  tempdir = tempfile.mkdtemp("convert-test")

def cleanup():
  if os.path.exists(tempdir):
    shutil.rmtree(tempdir)

CSV_CONTENT = "int,float,str\n1,2,3\n4,5.0,z\n"

@with_setup(setup, cleanup)
def test_from_csv_and_back():
  csv_file = tempdir + "/csv"
  final_file = tempdir + "/cols"
  column_file = tempdir + "/final"

  with open(csv_file, "w") as fd:
    fd.write(CSV_CONTENT)
    fd.close()
  
  taiga.columnar.convert_csv_to_tabular(csv_file, column_file, ",")
  taiga.columnar.convert_tabular_to_csv(column_file, final_file, "\t")

  with open(final_file) as fd:
    r = csv.reader(fd, delimiter="\t")
    rows = list(r)
  
  assert len(rows) == 3
  assert rows[0] == ["int", "float", "str"]
  assert rows[1] == ["1", "2.0", "3"]
  assert rows[2] == ["4", "5.0", "z"]
  