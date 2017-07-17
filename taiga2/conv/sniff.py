import csv
from collections import namedtuple

Column = namedtuple("Column", ["name", "type"])

class TypeAggregator:
    def __init__(self):
        self.couldBeFloat = True
        self.couldBeInt = True

    def add(self, v):
        if self.couldBeInt:
            try:
                int(v)
            except ValueError:
                self.couldBeInt = False

        if not self.couldBeInt and self.couldBeFloat:
            try:
                float(v)
            except ValueError:
                self.couldBeFloat = False

    def get_type(self):
        if self.couldBeInt:
            return int

        if self.couldBeFloat:
            return float

        return str


def sniff(filename, encoding, rows_to_check=None, delimiter="\t"):
    with open(filename, 'rU', encoding=encoding) as fd:
        r = csv.reader(fd, delimiter=delimiter)
        col_header = next(r)
        row = next(r)
        if len(col_header) == len(row):
            hasRowNames = False
        elif len(col_header) == (len(row) - 1):
            hasRowNames = True
        else:
            raise Exception("First and second rows have different numbers of columns")

        columnTypes = [TypeAggregator() for x in row]
        row_count = 0
        while rows_to_check is None or row_count < rows_to_check:
            for i, x in enumerate(row):
                columnTypes[i].add(x)

            try:
                row = next(r)
                row_count += 1
            except StopIteration:
                break

    if hasRowNames:
        del columnTypes[0]

    columns = [Column(col_header[i], columnTypes[i].get_type()) for i in range(len(columnTypes))]

    return hasRowNames, columns


