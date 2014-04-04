import sqlite3
from collections import namedtuple
import csv

Column = namedtuple("Column", ["name", "type"])

def sniff(filename, rows_to_check=100):
  with open(filename) as fd:
    r = csv.reader(fd)
    col_header = r.next()
    row = r.next()
    if len(col_header) == len(row):
      hasRowNames = False
    elif len(col_header) == (len(row)-1):
      hasRowNames = True
    else:
      raise Exception("First and second rows have different numbers of columns")
    
    columnValues = [[] for x in row]
    for row_count in xrange(rows_to_check):
      for i, x in enumerate(row):
        columnValues[i].append(x)

      try:
        row = r.next()
      except StopIteration:
        break

  if hasRowNames:
    del columnValues[0]
    
  columns = [Column(col_header[i], determine_type(columnValues[i])) for i in xrange(len(columnValues))]

  return hasRowNames, columns

def determine_type(values):
  couldBeFloat = True
  couldBeInt = True
  for v in values:
    if couldBeInt:
      try:
        int(v)
      except ValueError:
        couldBeInt = False

    if not couldBeInt and couldBeFloat:
      try:
        float(v)
      except ValueError:
        couldBeFloat = False
    
    if not couldBeFloat and not couldBeInt:
      break

  if couldBeInt:
    return int

  if couldBeFloat:
    return float

  return str

type_to_sqlite_type = {str: 'text', float: 'real', int: 'integer'}

def escape_identifier(x):
  return "\"%s\"" % (x.replace("\"", "\"\""))

class TableWriter:
  def __init__(self, filename, columns):
    self.connection = sqlite3.connect(filename)
    self.db = self.connection.cursor()
    self.columns = columns
    self.db.execute("CREATE TABLE data (%s)" % (",".join(["%s %s" % (escape_identifier(c.name), type_to_sqlite_type[c.type]) for c in columns])))
    self.insert_stmt = "INSERT INTO data VALUES (%s)" % (",".join(["?"]*len(columns)),) 

  def add_rows(self, values):
    self.db.executemany(self.insert_stmt, values)

  def close(self):
    self.connection.commit()
    self.db.close()
    self.connection.close()

class TableReader:
  def __init__(self, filename):
    self.connection = sqlite3.connect(filename)
    self.db = self.connection.cursor()

  def rows(self, column_names):
    column_clause = ",".join([escape_identifier(c) for c in column_names])
    self.db.execute("SELECT %s FROM data" % (column_clause,))
    for row in self.db.fetchall():
      yield row

  def close(self):
    self.db.close()
    self.connection.close()
