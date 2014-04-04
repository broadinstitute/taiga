class Predicate(object):
  def is_true(self):
    raise Exception("unimp")

  def get_columns(self):
    raise Exception("unimp")

class InPred(object):
  def __init__(self, name, values):
    self.values = values
    self.name = name
    
  def bind_predicate(self, cursorMap):
    cursor = cursorMap[self.name]
    values = self.values
    return lambda: cursor.get_value() in values

class AndPred(object):
  def __init__(self, preds):
    self.preds = preds

  def bind_predicate(self, cursorMap):
    and_list = [p.bind_predicate(cursorMap) for p in self.preds]
    def all_true():
      for p in and_list:
        if not p():
          break
      return True
    return all_true

class ColumnCursor(object):
  def __init__(self, values):
    self.index = 0
    
  def next(self):
    self.index += 1

  def get_value(self):
    return self.values[index]

class Serializer:
  def to_buffer(self, values):
    raise Exception("unimp")
  def from_buffer(self, array):
    " return a ColumnCursor "
    raise Exception("unimp")

# Block length (4b)
# Column lengths (4b * column_count)
# Column 1...
# Column 2...
# Column 3...

def persist_block(fd, column_persisters, values):
  column_lengths = []
  length_table_offset = fd.offset()
  write_block_header(fd, len(values), column_lengths)
  
  for i, cp in enumerate(column_persisters):
    column_values = [row[i] for row in values]
    column_buffer = cp.to_buffer(column_values)
    column_compressed = zlib.compress(column_buffer)
    column_lengths.append(len(column_compressed))
    fd.write(column_compressed)

  next_block = fd.offset()
  fd.seek(length_table_offset)
  write_block_header(fd, len(values), column_lengths)
  fd.seek(next_block)

def compute_column_offsets(base_offset, column_lengths):
  column_offsets = []
  cur_offset = base_offset
  for i, length in enumerate(column_lengths):
    column_offsets[i] = cur_offset
    cur_offset += length
  return column_offsets

def read_block(fd, column_count, columns):
  'columns: list of (column_index, persister) tuples'
  base_offset = fd.offset()
  cursors = []
  row_count, column_lengths = read_block_header(fd)

  column_offsets = compute_column_offsets(base_offset, column_lengths)
  for column_index, column_persister in columns:
    
    fd.seek(column_offsets[column_index])
    column_compressed = fd.read(column_lengths[column_index])
    column_buffer = zlib.decompress(column_compressed)
    column_cursor = column_persister.from_buffer(column_buffer)
    cursors.append(column_cursor)
  
  return row_count, cursors

def select_from_cursors(all_columns, projection, predicate, row_count):
  for i in xrange(row_count):
    if predicate.is_true():
      yield [c.get_value() for c in projection]
    
    for c in all_columns:
      c.next()

def select(fd, column_count, columns, bind_predicate):
  while True:
    next_block = read_block(fd, column_count, columns)
    if next_block == None:
      break

    row_count, cursors = next_block
    predicate = bind_predicate(cursors)
    projection = [cursors[i] for i in project_columns_indices]
    for row in select_from_cursors(cursors, projection, predicate, row_count):
      yield row

def read_metadata(fd):
  ...
  return column_definitions
  
def execute_query(fd, select_names, predicate):
  column_definitions = read_metadata(fd)
  columns_to_extract = []
  
  needed_columns = list(set(predicate.get_columns()) + set(select_names))
  name_to_index = dict( [(name, i) for i, k in enumerate(needed_columns)] )
  columns_to_extract = []
  for name in needed_columns:
    definition = column_definitions[name]
    columns_to_extract.append( (definition.index, definition.persister) )
  
  def bind_predicate(cursors):
    # go from indexed list of cursors to named map of cursors to perform binding
    cursor_map = {}
    for name in needed_columns:
      cursor_map[name] = cursors[name_to_index[name]]
    predicate.bind_predicate(cursor_map)
  
  select(fd, len(column_definitions), columns_to_extract, bind_predicate)
