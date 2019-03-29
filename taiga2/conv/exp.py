import csv
import os
import h5py
import subprocess

from taiga2.conv import columnar
from taiga2.conv.util import _to_string_with_nan_mask, r_escape_str
from taiga2.conv.columnar import columnar_to_rds

# Methods for converting internal formats (HDF5 or columnar) to all other formats (GCT, rds, tsv, csv)

# aim for about 50MB per block, consisting of doubles which are 8 bytes each
DEFAULT_MAX_ELEMENTS_PER_BLOCK=int(50*1e6//8)

def hdf5_to_rds(progress, hdf5_path, temp_file_generator, max_elements_per_block=DEFAULT_MAX_ELEMENTS_PER_BLOCK, progress_update=lambda x: None):
    "returns a list of filenames that were written"

    # estimate how many rows we can pack into a single rds file
    r = h5py.File(hdf5_path, "r")
    try:
        column_count = len(r["dim_1"])
        row_count = len(r["dim_0"])
        rows_per_block = max_elements_per_block // column_count
        block_count = (row_count + rows_per_block - 1) // rows_per_block

        assert rows_per_block > 0
    finally:
        r.close()


    generated_files = []
    for block_index in range(block_count):
        progress_update("Converting block {} out of {}".format(block_index, block_count))
        destination_file = temp_file_generator()
        script = ("""library(rhdf5);
            fn <- {};
            dst.fn <- {};
            rows.per.block <- {};
            i <- {};
            dim.0 <- make.unique(h5read(fn, '/dim_0'));
            dim.1 <- make.unique(h5read(fn, '/dim_1'));
            columns <- length(dim.1);
            rows <- length(dim.0);
            first.row.in.this.block <- rows.per.block*i+1;
            last.row.in.this.block <- min(rows.per.block*(i+1), rows);
            rows.in.this.block <- last.row.in.this.block - first.row.in.this.block + 1;
            cat("first.row.in.this.block", first.row.in.this.block, "\\n")
            cat("last.row.in.this.block", last.row.in.this.block, "\\n")
            data <- t(h5read(fn,'/data', start=c(1,first.row.in.this.block), count=c(columns, rows.in.this.block)));
            dimnames(data) <- list(dim.0[first.row.in.this.block:last.row.in.this.block], dim.1);
            data[is.nan(data)] <- NA;
            saveRDS(data, file=dst.fn)
            """.format(r_escape_str(hdf5_path), r_escape_str(destination_file), rows_per_block, block_index).encode("utf8"))

        with open("dump", "wb") as fd:
            fd.write(script)

        handle = subprocess.Popen(["R", "--vanilla"], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)
        stdout, stderr = handle.communicate(script)
        if handle.returncode != 0:
            raise Exception("R process failed: %s\n%s" % (stdout, stderr))

        generated_files.append(destination_file)

    progress_update("Finished converting {} blocks".format(block_count))

    return generated_files

def _get_matrix_dim_names(f, dedup_headers):
    row_header = [x.decode('utf8') for x in f['dim_0']]
    col_header = [x.decode('utf8') for x in f['dim_1']]

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

def _hdf5_to_tcsv(progress, src_path, temp_file_generator, delimiter, dedup_headers=False):
    f = h5py.File(src_path, "r")
    destination_file = temp_file_generator()
    with open(destination_file, "w") as fd_out:
        w = csv.writer(fd_out, delimiter=delimiter)

        data = f['data']
        row_header, col_header = _get_matrix_dim_names(f, dedup_headers)

        assert len(row_header) == data.shape[0], "row header length is {} but data has {} rows".format(len(row_header), data.shape[0])
        assert len(col_header) == data.shape[1], "column header length is {} but data has {} columns".format(len(row_header), data.shape[1])

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

        data = f['data']
        row_header, col_header = _get_matrix_dim_names(f, False)
        if 'gct_description' in f:
          descriptions = [x.decode('utf8') for x in f['gct_description']]
        else:
          descriptions = row_header

        w.writerow(["#1.2"])
        w.writerow([str(len(row_header)), str(len(col_header))])
        w.writerow(["Name", "Description"]+col_header)
        row_count = len(row_header)
        for i in range(row_count):
            row = data[i, :]
            w.writerow([row_header[i], descriptions[i]] + [_to_string_with_nan_mask(x) for x in row])

    return [destination_file]
