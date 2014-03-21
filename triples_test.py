import triples
from triples import Ref
import os

def create_empty():
  if os.path.exists("sample.sqlite3"):
    os.unlink("sample.sqlite3")
  return triples.TripleStore("sample.sqlite3")

def test_insert_and_query():
  ts = create_empty()
  
  ts.insert(Ref("x"), Ref("y"), Ref("z"))
  ts.insert(Ref("a"), Ref("y"), Ref("z"))
  ts.insert(Ref("a"), Ref("b"), Ref("z"))
  
  assert ts.find(Ref("x"), None, None) == [(Ref("x"),Ref("y"),Ref("z"))]
  assert ts.find(Ref("x"), Ref("y"), None) == [(Ref("x"),Ref("y"),Ref("z"))]
  assert ts.find(Ref("x"), Ref("y"), Ref("z")) == [(Ref("x"),Ref("y"),Ref("z"))]
  
  ts.close()

def test_insert_dups():
  ts = create_empty()
  
  ts.insert(Ref("x"), Ref("y"), Ref("z"))
  ts.insert(Ref("a"), Ref("y"), Ref("z"))
  ts.insert(Ref("a"), Ref("b"), Ref("z"))
  
  assert ts.find(Ref("x"), None, None) == [(Ref("x"),Ref("y"),Ref("z"))]
  assert ts.find(Ref("x"), Ref("y"), None) == [(Ref("x"),Ref("y"),Ref("z"))]
  assert ts.find(Ref("x"), Ref("y"), Ref("z")) == [(Ref("x"),Ref("y"),Ref("z"))]
  
  ts.close()
  

def test_delete():
  ts = create_empty()
  
  ts.insert(Ref("x"), Ref("y"), Ref("z"))
  ts.insert(Ref("a"), Ref("y"), Ref("z"))
  ts.delete(Ref("x"), Ref("y"), Ref("z"))

  assert ts.find(None, None, Ref("z")) == [(Ref("a"),Ref("y"),Ref("z"))]
