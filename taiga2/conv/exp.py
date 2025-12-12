import csv
import os
import h5py
import subprocess

from taiga2.conv import columnar
from taiga2.conv.util import _to_string_with_nan_mask, r_escape_str

# Methods for converting internal formats (HDF5 or columnar) to all other formats (GCT, rds, tsv, csv)

# aim for about 50MB per block, consisting of doubles which are 8 bytes each
DEFAULT_MAX_ELEMENTS_PER_BLOCK = int(50 * 1e6 // 8)


def _get_matrix_dim_names(f, dedup_headers):
    row_header = [x.decode("utf8") for x in f["dim_0"]]
    col_header = [x.decode("utf8") for x in f["dim_1"]]

    if dedup_headers:

        def dedup(l):
            value_count = {}
            for i in range(len(l)):
                v = l[i]
                if v in value_count:
                    l[i] = "%s.%d" % (l[i], value_count[v])
                    value_count[v] += 1
                else:
                    value_count[v] = 1

        dedup(row_header)
        dedup(col_header)
    return row_header, col_header


def _hdf5_to_tcsv(
    progress, src_path, temp_file_generator, delimiter, dedup_headers=False
):
    f = h5py.File(src_path, "r")
    destination_file = temp_file_generator()
    with open(destination_file, "w") as fd_out:
        w = csv.writer(fd_out, delimiter=delimiter)

        data = f["data"]
        row_header, col_header = _get_matrix_dim_names(f, dedup_headers)

        assert (
            len(row_header) == data.shape[0]
        ), "row header length is {} but data has {} rows".format(
            len(row_header), data.shape[0]
        )
        assert (
            len(col_header) == data.shape[1]
        ), "column header length is {} but data has {} columns".format(
            len(row_header), data.shape[1]
        )

        w.writerow([""] + col_header)
        row_count = len(row_header)
        for i in range(row_count):
            row = data[i, :]
            w.writerow([row_header[i]] + [_to_string_with_nan_mask(x) for x in row])

    return [destination_file]


def hdf5_to_csv(progress, src_path, temp_file_generator):
    return _hdf5_to_tcsv(progress, src_path, temp_file_generator, ",")


def hdf5_to_tsv(progress, src_path, temp_file_generator):
    return _hdf5_to_tcsv(progress, src_path, temp_file_generator, "\t")


def hdf5_to_gct(progress, src_path, temp_file_generator):
    f = h5py.File(src_path, "r")
    destination_file = temp_file_generator()
    with open(destination_file, "w") as fd_out:
        w = csv.writer(fd_out, delimiter="\t")

        data = f["data"]
        row_header, col_header = _get_matrix_dim_names(f, False)
        if "gct_description" in f:
            descriptions = [x.decode("utf8") for x in f["gct_description"]]
        else:
            descriptions = row_header

        w.writerow(["#1.2"])
        w.writerow([str(len(row_header)), str(len(col_header))])
        w.writerow(["Name", "Description"] + col_header)
        row_count = len(row_header)
        for i in range(row_count):
            row = data[i, :]
            w.writerow(
                [row_header[i], descriptions[i]]
                + [_to_string_with_nan_mask(x) for x in row]
            )

    return [destination_file]
