import csv
from collections import namedtuple

Column = namedtuple("Column", ["name", "type"])

def sniff(filename, rows_to_check=100):
  with open(filename) as fd:
    r = csv.reader(fd, delimiter="\t")
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
