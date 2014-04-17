import sqlmeta
from sqlmeta import Ref

def test_find_perfect_match():
  def find_stmt(s, p, o):
    assert s == Ref("a")
    assert p == Ref("b")
    assert o == "c"
    return [(Ref("a"), Ref("b"), "c")]
  
  assert sqlmeta.exec_sub_stmt_query((
    ({"id":"a"}, {"id":"b"}, "c"),
  ), find_stmt, {}) == [{}]

def test_find_with_variable():
  def find_stmt(s, p, o):
    assert s == Ref("a")
    assert p == Ref("b")
    assert o == None
    return [(Ref("a"), Ref("b"), "c")]
  
  assert sqlmeta.exec_sub_stmt_query((
    ({"id":"a"}, {"id":"b"}, {"var": "x"}),
  ), find_stmt, {}) == [{"x":"c"}]

def test_constrained_variable():
  def find_stmt(s, p, o):
    if s == Ref("a") and p == Ref("b") and o == None:
      return [(Ref("a"), Ref("b"), "c")]
    elif s == None and p == Ref("d") and o == "c":
      return [(Ref("e"), Ref("d"), "c")]
    else:
      raise Exception("unknown %s" % repr((s,p,o)))
  
  assert sqlmeta.exec_sub_stmt_query((
    ({"id":"a"}, {"id":"b"}, {"var": "x"}),
    ({"var":"y"}, {"id":"d"}, {"var": "x"}),
  ), find_stmt, {}) == [{"x":"c","y":Ref("e")}]
