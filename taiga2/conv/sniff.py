import csv
from collections import namedtuple

Column = namedtuple("Column", ["name", "type"])

def sniff(filename, rows_to_check=None, delimiter="\t"):
    with open(filename, 'rU') as fd:
        r = csv.reader(fd, delimiter=delimiter)
        col_header = r.next()
        row = r.next()
        if len(col_header) == len(row):
            hasRowNames = False
        elif len(col_header) == (len(row) - 1):
            hasRowNames = True
        else:
            raise Exception("First and second rows have different numbers of columns")

        columnValues = [[] for x in row]
        row_count = 0
        while rows_to_check is None or row_count < rows_to_check:
            for i, x in enumerate(row):
                columnValues[i].append(x)

            try:
                row = r.next()
                row_count += 1
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
