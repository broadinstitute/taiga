from taiga2.tests.datafile_test import StubProgress
from taiga2.conv import (
    hdf5_to_csv,
    csv_to_hdf5,
    csv_to_columnar,
    columnar_to_csv,
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
