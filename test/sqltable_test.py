import tempfile
import os
from nose import with_setup
from taiga import sqltable

temp_filename = None

def find_temp_file():
  global temp_filename
  
  fd = tempfile.NamedTemporaryFile(delete=False)
  temp_filename = fd.name
  fd.close()
  os.unlink(temp_filename)

def cleanup_temp_file():
  if os.path.exists(temp_filename):
    os.unlink(temp_filename)

@with_setup(find_temp_file, cleanup_temp_file)
def test_basic_usages():
  t = sqltable.TableWriter(temp_filename, [sqltable.Column("x", int), sqltable.Column("y", float), sqltable.Column("z", str)])
  data = (
    (1, 2.1, "three"),
    (4, 5.1, "six"),
    (7, 8.1, "nine"),
  )
  t.add_rows(data)
  t.close()
  
  t = sqltable.TableReader(temp_filename)
  rows = list( t.rows(["x", "y", "z"]) )
  rows.sort()
  rows == list(data)
  t.close()

def test_sniff():
  hasRowHeader, columns = sqltable.sniff("test_data/test_sniff.csv")
  assert not hasRowHeader 
  assert len(columns) == 3
  print columns
  assert columns[0].name == 'a'
  assert columns[0].type == int
  assert columns[1].name == 'b'
  assert columns[1].type == float
  assert columns[2].name == 'c'
  assert columns[2].type == str 
  