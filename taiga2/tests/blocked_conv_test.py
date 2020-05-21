from taiga2.tests.datafile_test import StubProgress
from taiga2.conv import (
    hdf5_to_csv,
    csv_to_hdf5,
    csv_to_columnar,
    columnar_to_csv,
    hdf5_to_gct,
    columnar_to_rds,
)
import os
import sys

# tests to make sure processing in chunks/blocks is working correctly by roundtripping data through converters

tall_matrix_filename = "tall_matrix.csv"
tall_matrix_file_path = os.path.join(
    os.path.dirname(sys.modules[__name__].__file__), "test_files", tall_matrix_filename
)

tall_table_filename = "tall_table.csv"
tall_table_file_path = os.path.join(
    os.path.dirname(sys.modules[__name__].__file__), "test_files", tall_table_filename
)

tall_gct_filename = "tall_matrix.gct"
tall_gct_file_path = os.path.join(
    os.path.dirname(sys.modules[__name__].__file__), "test_files", tall_gct_filename
)


def test_csv_to_hdf5(tmpdir):
    dst_hdf5_file = str(tmpdir.join("out.hdf5"))
    dest_csv = str(tmpdir.join("dest.csv"))

    # convert to hdf5 and back, two rows at a time
    csv_to_hdf5(StubProgress(), tall_matrix_file_path, dst_hdf5_file, rows_per_block=2)
    hdf5_to_csv(StubProgress(), dst_hdf5_file, lambda: dest_csv)

    assert open(tall_matrix_file_path, "rt").read() == open(dest_csv, "rt").read()


def test_csv_to_columnar(tmpdir):
    dst_hdf5_file = str(tmpdir.join("out.hdf5"))
    dest_csv = str(tmpdir.join("dest.csv"))

    # convert to hdf5 and back, two rows at a time
    csv_to_columnar(
        StubProgress(), tall_table_file_path, dst_hdf5_file, rows_per_block=2
    )
    columnar_to_csv(StubProgress(), dst_hdf5_file, lambda: dest_csv)

    assert open(tall_table_file_path, "rt").read() == open(dest_csv, "rt").read()


def test_large_columnar_to_rds(tmpdir):
    import csv

    src_csv = str(tmpdir.join("source.csv"))
    dst_columnar = str(tmpdir.join("source.columnar"))

    # make sizable source file
    with open(src_csv, "wt") as fd:
        w = csv.writer(fd)
        w.writerow(["X" + str(i) for i in range(100)])
        for i in range(500):
            w.writerow(["V"] * 100)

    filename_count = [0]

    def temp_file_generator():
        f = str(tmpdir.join("t" + str(filename_count[0])))
        filename_count[0] += 1
        return f

    csv_to_columnar(StubProgress(), src_csv, dst_columnar)
    # run, with max bytes set to approximate that we should write out 4 files
    files = columnar_to_rds(
        StubProgress(), dst_columnar, temp_file_generator, max_bytes=200 * 500 / 3
    )
    assert len(files) == 4
