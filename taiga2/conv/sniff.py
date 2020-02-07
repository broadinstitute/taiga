import csv
from collections import namedtuple
from typing import Dict, Optional

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
    with open(filename, "rU", encoding=encoding) as fd:
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

    columns = [
        Column(col_header[i], columnTypes[i].get_type())
        for i in range(len(columnTypes))
    ]

    return hasRowNames, columns


# Taken from pandas.read_csv's list of na_values
NA_STRINGS = [
    "",
    "#N/A",
    "#N/A N/A",
    "#NA",
    "-1.#IND",
    "-1.#QNAN",
    "-NaN",
    "-nan",
    "1.#IND",
    "1.#QNAN",
    "<NA>",
    "N/A",
    "NA",
    "NULL",
    "NaN",
    "n/a",
    "nan",
    "null",
]


class TypeAggregator2:
    def __init__(self):
        self.couldBeFloat = True

    def add(self, v):
        if v in NA_STRINGS:
            return

        if self.couldBeFloat:
            try:
                float(v)
            except ValueError:
                self.couldBeFloat = False

    def get_type(self):
        if self.couldBeFloat:
            return "float"

        return "str"


def sniff2(filename: str, encoding: str, delimiter=",") -> Optional[Dict[str, str]]:
    with open(filename, "rU", encoding=encoding) as fd:
        r = csv.reader(fd, delimiter=delimiter)
        col_header = next(r)

        if len(set(col_header)) != len(col_header):
            raise Exception("Column names are not unique")

        try:
            row = next(r)
        except StopIteration:
            return None

        if len(col_header) == len(row):
            has_row_names = False
        elif len(col_header) == (len(row) - 1):
            has_row_names = True
        else:
            raise Exception("First and second rows have different numbers of columns")

        column_types = [TypeAggregator2() for x in row]
        while True:
            for i, x in enumerate(row):
                column_types[i].add(x)

            try:
                row = next(r)
            except StopIteration:
                break

    if has_row_names:
        del column_types[0]

    columns = {
        col_header[i]: column_types[i].get_type() for i in range(len(column_types))
    }

    return columns
