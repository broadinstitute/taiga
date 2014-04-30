import sqlite3
from collections import namedtuple
import csv

from sniff import Column
from sniff import sniff

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
