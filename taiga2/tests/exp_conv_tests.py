import subprocess

from taiga2.conv import exp
from taiga2.conv import imp
from taiga2.conv.util import r_escape_str
import csv

import pytest

def rds_to_csv(sources, dest):
    handle = subprocess.Popen(["R", "--vanilla"], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE)
    script_buf = []
    for source in sources:
        if len(script_buf) > 0:
            script_buf.append("data <- rbind(data, readRDS(%s));\n" % r_escape_str(source))
        else:
            script_buf.append("data <- readRDS(%s);\n" % r_escape_str(source))
    script_buf.append("write.table(data, file=%s, sep=',')" % r_escape_str(dest))
    stdout, stderr = handle.communicate("".join(script_buf).encode("utf8"))
    if handle.returncode != 0:
        raise Exception("R process failed: %s\n%s" % (stdout, stderr))

def write_sample_csv(csv_file, rows, columns):
    with open(csv_file, "wt") as fd:
        w = csv.writer(fd)
        w.writerow([""]+["c"+str(i) for i in range(columns)])
        next_value = 0
        for row_i in range(rows):
            row = ["r"+str(row_i)]
            for i in range(columns):
                row.append(next_value)
                next_value += 1
            next_value += 100
            w.writerow(row)
    fd.close()

def write_sample_table(csv_file, rows, columns):
    with open(csv_file, "wt") as fd:
        w = csv.writer(fd)
        w.writerow(["c"+str(i) for i in range(columns)])
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

@pytest.mark.parametrize("max_elements_per_block,expected_file_count", [
    (10000,1),
    (5*5, 2)
])
def test_hdf5_to_rds(tmpdir,max_elements_per_block,expected_file_count):
    # actually test this by round-tripping from csv to hdf5 to rds to csv to make sure that we can recapitulate what was
    # originally submitted

    original_csv = str(tmpdir.join("t.csv"))
    hdf5_file = str(tmpdir.join("t.hdf5"))
    final_csv = str(tmpdir.join("final.csv"))

    write_sample_csv(original_csv, 10, 5)

    imp.tcsv_to_hdf5(ProgressStub(), original_csv, hdf5_file)
    files = exp.hdf5_to_rds(hdf5_file, str(tmpdir), max_elements_per_block=max_elements_per_block)
    assert len(files) == expected_file_count
    rds_to_csv(files, final_csv)

@pytest.mark.parametrize("max_rows,expected_file_count", [
    (None,1),
    (5, 2)
])
def test_columnar_to_rds(tmpdir,max_rows,expected_file_count):
    # actually test this by round-tripping from csv to columnar to rds to csv to make sure that we can recapitulate what was
    # originally submitted

    original_csv = str(tmpdir.join("t.csv"))
    columnar_file = str(tmpdir.join("t.columnar"))
    final_csv = str(tmpdir.join("final.csv"))

    write_sample_table(original_csv, 10, 5)

    imp.tcsv_to_columnar(ProgressStub(), original_csv, columnar_file, ",")
    files = exp.columnar_to_rds(columnar_file, str(tmpdir), max_rows=max_rows)
    assert len(files) == expected_file_count
    rds_to_csv(files, final_csv)
