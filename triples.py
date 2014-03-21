# triple
# subject predicate object -> stmt
# ref | str -> object 
# ref -> subject
# ref -> predicate

import sqlite3
import os
from collections import namedtuple

Ref = namedtuple("Ref", ["id"])

def prefix_object(object):
  if isinstance(object, Ref):
    prefixed_obj = "#"+object.id
  else:
    prefixed_obj = "!"+object
  return prefixed_obj

def unprefix_object(object_str):
  if object_str[0] == "#":
    return Ref(object_str[1:])
  else:
    return object_str[1:]

class TripleStore:
  def __init__(self, filename):
    new_db = not os.path.exists(filename)
    self.connection = sqlite3.connect(filename)
    self.cursor = self.connection.cursor()
    if new_db:
      stmts = [
        "create table statements (subject text, predicate text, object text)",
        "create index idx1 on statements (subject, predicate, object)",
        "create index idx2 on statements (object, predicate, subject)",
        "create index idx3 on statements (predicate, subject, object)",
        ]
      for stmt in stmts:
        self.cursor.execute(stmt)

  def insert(self, subject, predicate, object):
    self.cursor.execute("insert into statements values (?, ?, ?)", (subject.id, predicate.id, prefix_object(object)))
    self.connection.commit()
    
  def delete(self, subject, predicate, object):
    self.cursor.execute("delete from statements where subject = ? and predicate = ? and object = ?", (subject.id, predicate.id, prefix_object(object)))
    self.connection.commit()

  def find(self, subject, predicate, object):
    predicates = []
    parameters = []
    if subject != None:
      predicates.append("subject = ?")
      parameters.append(subject.id)
    if predicate != None:
      predicates.append("predicate = ?")
      parameters.append(predicate.id)
    if object != None:
      predicates.append("object = ?")
      parameters.append(prefix_object(object))
    
    query = "select * from statements where %s" % (" AND ".join(predicates))
    self.cursor.execute(query, parameters)
    return [ (Ref(s), Ref(p), unprefix_object(o)) for s, p, o in self.cursor.fetchall() ]

  def close(self):
    self.cursor.close()
    self.connection.close()
    