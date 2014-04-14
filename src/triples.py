# triple
# subject predicate object -> stmt
# ref | str -> object 
# ref -> subject
# ref -> predicate

import sqlite3
import os
from collections import namedtuple

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

class TripleStore:
  def __init__(self, filename):
    new_db = not os.path.exists(filename)
    self.connection = sqlite3.connect(filename)
    self.cursor = self.connection.cursor()
    if new_db:
      stmts = [
        "create table statements (subject text, predicate text, object_type integer, object)"
        ]
      for stmt in stmts:
        self.cursor.execute(stmt)

  def insert(self, subject, predicate, object):
    object_type, object_str = prefix_object(object)
    self.cursor.execute("insert into statements (subject, predicate, object_type, object) values (?, ?, ?, ?)", (subject.id, predicate.id, object_type, object_str))
    self.connection.commit()
    
  def delete(self, subject, predicate, object):
    object_type, object_str = prefix_object(object)
    self.cursor.execute("delete from statements where subject = ? and predicate = ? and object = ? and object_type = ?", (subject.id, predicate.id, object_str, object_type))
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
      predicates.append("object_type = ? and object = ?")
      parameters.extend(prefix_object(object))
    
    query = "select subject, predicate, object_type, object from statements where %s" % (" AND ".join(predicates))
    self.cursor.execute(query, parameters)
    return [ (Ref(s), Ref(p), unprefix_object(o,ot)) for s, p, ot, o in self.cursor.fetchall() ]

  def close(self):
    self.cursor.close()
    self.connection.close()
