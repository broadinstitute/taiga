import subprocess

from taiga2.conv import exp
from taiga2 import conv
from taiga2.conv.util import r_escape_str
import csv

import pytest
from taiga2.conv.util import make_temp_file_generator


def write_sample_csv(csv_file, rows, columns):
    with open(csv_file, "wt") as fd:
        w = csv.writer(fd)
        w.writerow([""] + ["c" + str(i) for i in range(columns)])
        next_value = 0
        for row_i in range(rows):
            row = ["r" + str(row_i)]
            for i in range(columns):
                row.append(next_value)
                next_value += 1
            next_value += 100
            w.writerow(row)
    fd.close()


def write_sample_table(csv_file, rows, columns):
    with open(csv_file, "wt") as fd:
        w = csv.writer(fd)
        w.writerow(["c" + str(i) for i in range(columns)])
        next_value = 0
        for row_i in range(rows):
            row = []
            for i in range(columns):
                row.append(next_value)
                next_value += 1
            next_value += 100
            w.writerow(row)
    fd.close()


class ProgressStub:
    def progress(self, *args, **kwargs):
        print("progress", args, kwargs)

    def failed(self, *args, **kwargs):
        print("failed", args, kwargs)
