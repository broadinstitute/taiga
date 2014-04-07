import cStringIO
import struct
import zlib

class Predicate(object):
  def create_evaluator(self, cursorMap):
    raise Exception("unimp")

  def get_columns(self):
    raise Exception("unimp")

class InPred(object):
  def __init__(self, name, values):
    self.values = values
    self.name = name
    
  def create_evaluator(self, cursorMap):
    cursor = cursorMap[self.name]
    assert cursor != None, "No cursor for %s in %s" % (repr(self.name), repr(cursorMap))
    values = self.values
    
    def is_satified():
      #print "is_satified", cursor.get_value(), values
      return cursor.get_value() in values
    return is_satified
    
  def get_columns(self):
    return [self.name]

class AndPred(object):
  def __init__(self, preds):
    self.preds = preds

  def create_evaluator(self, cursorMap):
    and_list = [p.create_evaluator(cursorMap) for p in self.preds]
    def all_true():
      for p in and_list:
        if not p():
          break
      return True
    return all_true

  def get_columns(self):
    return sum([p.get_columns() for p in self.preds])

class ColumnCursor(object):
  def __init__(self, values):
    self.index = 0
    self.values = values
    
  def next(self):
    self.index += 1

  def get_value(self):
    return self.values[self.index]

def write_int(output, n):
  output.write(struct.pack("I", n))

def read_int(fd):
  buffer = fd.read(4)
  if len(buffer) == 0:
    return None
  return struct.unpack("I", buffer)[0]

def write_str(output, s):
  write_int(output, len(s))
  output.write(s)

def read_str(fd):
  length = read_int(fd)
  if length == None:
    return None
  return fd.read(length)
  
class StringSerializer:
  def to_buffer(self, values):
    output = cStringIO.StringIO()
    for s in values:
      write_str(output, s)
    return output.getvalue()

  def from_buffer(self, array):
    fd = cStringIO.StringIO(array)
    values = []
    while True:
      v = read_str(fd)
      if v == None:
        break
      values.append(v)
    return ColumnCursor(values)

# Block length (4b)
# Column lengths (4b * column_count)
# Column 1...
# Column 2...
# Column 3...

def write_block_header(fd, row_count, column_lengths):
  write_int(fd, row_count)
  write_int(fd, len(column_lengths))
  for length in column_lengths:
    write_int(fd, length)
  #print "after write header", fd.tell()

def read_block_header(fd):
  row_count = read_int(fd)
  if row_count == None:
    return None
  #print "row count %d" % row_count
  column_count = read_int(fd)
  assert column_count < 1000
  #print "reading %d columns" % column_count
  column_lengths = []
  for i in xrange(column_count):
    column_lengths.append(read_int(fd))
  #print "after read header", fd.tell()
  return row_count, column_lengths

def persist_block(fd, column_persisters, values):
  column_lengths = []
  length_table_offset = fd.tell()
  write_block_header(fd, len(values), [0] * len(column_persisters))
  
  column_offsets = []
  for i, cp in enumerate(column_persisters):
    column_offsets.append(fd.tell())
    column_values = [row[i] for row in values]
    column_buffer = cp.to_buffer(column_values)
    column_compressed = zlib.compress(column_buffer)
    column_lengths.append(len(column_compressed))
    fd.write(column_compressed)
  #print "wrote col offsets", column_offsets

  next_block = fd.tell()
  fd.seek(length_table_offset)
  write_block_header(fd, len(values), column_lengths)
  fd.seek(next_block)
  #print column_lengths

def compute_column_offsets(base_offset, column_lengths):
  column_offsets = []
  cur_offset = base_offset
  for i, length in enumerate(column_lengths):
    column_offsets.append(cur_offset)
    cur_offset += length
  return column_offsets

def read_block(fd, column_count, columns):
  'columns: list of (column_index, persister) tuples'
  cursors = []
  pair = read_block_header(fd)
  if pair == None:
    return None
  row_count, column_lengths = pair
  base_offset = fd.tell()

  column_offsets = compute_column_offsets(base_offset, column_lengths)

  #print "column_lengths", column_lengths
  #print "column_offsets", column_offsets

  for column_index, column_persister in columns:
    
    fd.seek(column_offsets[column_index])
    column_compressed = fd.read(column_lengths[column_index])
    column_buffer = zlib.decompress(column_compressed)
    column_cursor = column_persister.from_buffer(column_buffer)
    cursors.append(column_cursor)
  
  # seek past the end of all data
  fd.seek(column_offsets[-1] + column_lengths[-1])
  
  return row_count, cursors

def select_from_cursors(all_columns, projection, predicate, row_count):
  for i in xrange(row_count):
    #print "evaluating for row %d, %s" % (i, [c.get_value() for c in projection])
    if predicate():
      yield [c.get_value() for c in projection]
    
    for c in all_columns:
      c.next()

def select(fd, column_count, columns, projection_indices, bind_predicate):
  'columns is list of (index, persister)'
  while True:
    next_block = read_block(fd, column_count, columns)
    if next_block == None:
      break

    row_count, cursors = next_block
    predicate = bind_predicate(cursors)
    projection = [cursors[index] for index in projection_indices]
    for row in select_from_cursors(cursors, projection, predicate, row_count):
      yield row

  
def execute_query(fd, select_names, predicate):
  column_definitions = read_column_definitions(fd)
  columns_to_extract = []
  
  needed_columns = list(set(predicate.get_columns()).union(select_names))
  name_to_index = dict( [(name, i) for i, name in enumerate(needed_columns)] )
  columns_to_extract = []
  for name in needed_columns:
    definition = column_definitions[name]
    columns_to_extract.append( (definition.index, definition.persister) )
  
  def bind_predicate(cursors):
    # go from indexed list of cursors to named map of cursors to perform binding
    cursor_map = {}
    #print "name to index", name_to_index
    #print "cursors", cursors
    for name in needed_columns:
      #print "name=%s" % name
      cursor_map[name] = cursors[name_to_index[name]]
    return predicate.create_evaluator(cursor_map)
  
  projection_indices = [ name_to_index[name] for name in select_names ]
  for row in select(fd, len(column_definitions), columns_to_extract, projection_indices, bind_predicate):
    yield row

def write_column_definitions(fd, name_type_pairs):
  fd.write(struct.pack("I", len(name_type_pairs)))
  for name, col_type in name_type_pairs:
    write_str(fd, name)
    write_str(fd, col_type.__name__)
from collections import namedtuple
ColumnDef = namedtuple("ColumnDef", ["name", "ty", "index", "persister"])
class TableInfo:
  def __init__(self, columns):
    self.columns = columns
    self.by_name = dict([(c.name, c) for c in columns])
    
  def __getitem__(self, key):
    return self.by_name[key]
  
  def __len__(self):
    return len(self.columns)

def read_column_definitions(fd):
  col_count_buffer = fd.read(4)
  col_count = struct.unpack("I", col_count_buffer)[0]
  columns = []
  for i in xrange(col_count):
    name = read_str(fd)
    type_name = read_str(fd)
    assert type_name == 'str'
    columns.append( ColumnDef(name, str, i, StringSerializer()) )
  return TableInfo(columns)

fn = "/Users/pmontgom/data/fh_WM793_SKIN.maf.ccle.annotated"
#fn = "sample.maf"
input = open(fn)
import csv
import os
if not os.path.exists("dump"):
#if True:
  r = csv.reader(input, delimiter="\t")
  header = r.next()
  persisters = [StringSerializer() for i in xrange(len(header))]

  rows = []
  for row in r:
    rows.append(row)

  fd = open("dump","w")
  write_column_definitions(fd, [(header[i], str) for i in xrange(len(header))])
  persist_block(fd, persisters, rows)
  fd.close()

print "transformed"
fd = open("dump")
for row in execute_query(fd, ["Hugo_Symbol"], InPred("Entrez_Gene_Id", set(["653635"]))):
  print "row", row
fd.close()

