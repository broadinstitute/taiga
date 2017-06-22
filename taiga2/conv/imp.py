import csv
import numpy as np
from taiga2.conv.util import ImportResult, shortened_list, get_file_sha256

DEFAULT_MAX_ELEMENTS_PER_BLOCK=1e6*50/8

# class ReadTextWithHash:
#     def __init__(self, file):
#         self.hash = hashlib.sha256()
#         self.file = file
#         self.line_generator = self._make_generator()
#
#     def _make_generator(self):
#         while True:
#             buffer = self.read(1024*1024)
#             if len(buffer) == 0:
#                 break
#
#
#     def __iter__(self):
#         return self
#
#     def __next__(self):
#         return next(self.textfile)
#
#     def readline(self):
#         return next(self.line_generator)
#
#     def read(self, length):
#         b = self.file.read(length)
#         assert isinstance(b, bytes)
#         self.hash.update(b)
#         return b.decode("utf8")
#
#     def sha256(self):
#         return self.hash.hexdigest()

def _get_csv_dims(progress, filename, dialect, encoding):
    hash = get_file_sha256(filename)
    with open(filename, "rU", encoding=encoding) as fd:
        r = csv.reader(fd, dialect)
        row_count = 0
        col_header = next(r)
        first_row = None

        for row in r:
            if first_row is None:
               first_row = row
            row_count += 1
            if row_count % 1000 == 0:
                message = "Scanning through file to determine size (line {})".format(row_count+1)
                progress.progress(message, None, row_count+1)

    return row_count, len(first_row) - 1, hash

def csv_to_hdf5(progress, src_csv_file, dst_hdf5_file, **kwargs):
    return tcsv_to_hdf5(progress, src_csv_file, dst_hdf5_file, csv.excel, **kwargs)

def tsv_to_hdf5(progress, src_csv_file, dst_hdf5_file, **kwargs):
    return tcsv_to_hdf5(progress, src_csv_file, dst_hdf5_file, csv.excel_tab, **kwargs)

def gct_to_hdf5(progress, src_gct_file, dst_hdf5_file, rows_per_block=None, max_size_per_block=DEFAULT_MAX_ELEMENTS_PER_BLOCK):
    sha256 = get_file_sha256(src_gct_file)

    with open(src_gct_file, 'rt') as gct:
        line = gct.readline().strip()
        assert line == "#1.2"
        r = csv.reader(gct, csv.excel_tab)
        dims = [int(x) for x in next(r)]
        row_count, col_count = dims

        col_header = next(r)
        # drop the id/description header column names
        col_header = col_header[2:]

        _validate_columns(progress, col_header)

        description_column = []

        def rows_without_description():
            while True:
                row = next(r)
                description_column.append(row[1])
                yield [row[0]] + row[2:]

        na_count, row_header = _convert_to_hdf5_file(row_count, col_count, col_header, csv.excel_tab, dst_hdf5_file, progress, rows_without_description(), rows_per_block, max_size_per_block, description_column=description_column)

    return _make_import_result(col_count, col_header, na_count, row_count, row_header, sha256)

def _validate_columns(progress, col_header):
    # validate to make sure no other column headers are blank.  We should communicate this to the submitted, but
    # doing it as a hard assertion for the time being.
    for i, x in enumerate(col_header):
        if x == '':
            message = "Column name for column {} was blank".format(i + 1, )
            progress.failed(message, None)
            raise Exception(message)

def _determine_col_header(tcsv, dialect, progress):
    tcsv.seek(0)
    r = csv.reader(tcsv, dialect)
    col_header = next(r)
    first_row = next(r)

    # Does the header line up with the number of columns in the row, or do we need to shift it by one? (Such as tables written by R)
    if len(col_header) == len(first_row):
        col_header = col_header[1:]
    else:
        if len(col_header) + 1 == len(first_row):
            pass
        else:
            message = "On line 2: Expected %d columns, but found %d columns." % (
                len(col_header), len(first_row))
            progress.failed(message, None)
            raise Exception(message)

    # jump back to the beginning
    tcsv.seek(0)
    r = csv.reader(tcsv, dialect)
    # this time skip the header
    next(r)
    return col_header, r


def tcsv_to_hdf5(progress, src_csv_file, dst_hdf5_file, dialect, rows_per_block=None, max_size_per_block=DEFAULT_MAX_ELEMENTS_PER_BLOCK, encoding="iso-8859-1"):
    # now we could resize the hdf5 matrix as necessary, or we can make two passes over the data.  Let's start with
    # dumb approach of walking over the data twice.

    with open(src_csv_file, 'rt') as tcsv:
        tcsv.seek(0)
        row_count, col_count, sha256 = _get_csv_dims(progress, src_csv_file, dialect, encoding)

        col_header, r = _determine_col_header(tcsv, dialect, progress)

        _validate_columns(progress, col_header)

        na_count, row_header = _convert_to_hdf5_file(row_count, col_count, col_header, dialect, dst_hdf5_file, progress, r, rows_per_block, max_size_per_block)

    return _make_import_result(col_count, col_header, na_count, row_count, row_header, sha256)


def _make_import_result(col_count, col_header, na_count, row_count, row_header, sha256):
    long_summary = "Column names: {}\nRow names: {}\n".format(shortened_list(col_header), shortened_list(row_header))
    return ImportResult(sha256=sha256, short_summary="{}x{} matrix, {} NAs".format(row_count, col_count, na_count),
                        long_summary=long_summary)


def _convert_to_hdf5_file(row_count, col_count, col_header, dialect, dst_hdf5_file, progress, r, rows_per_block, max_size_per_block, description_column=None):
    import h5py

    if rows_per_block is None:
        rows_per_block = int(max_size_per_block / col_count)
        assert rows_per_block > 0

    with h5py.File(dst_hdf5_file, 'w') as file_hdf5:
        data = file_hdf5.create_dataset("data", (row_count, col_count), "d")
        data.attrs['id'] = '0'

        row_index = 0
        row_header = []
        na_count = 0
        for block_row_header, block_data in _read_rows_in_chunks(row_index + 1, progress, dst_hdf5_file, col_header, r,
                                                                 rows_per_block, dialect):
            row_header.extend(block_row_header)

            # update data (the hdf5 matrix we're writing to) with the latest block
            block_end = row_index + len(block_row_header)

            # print("block_row_header", len(block_row_header))
            # print("block_data", np.array(block_data))
            # print("target", np.array(data[row_index:block_end,:]))

            block_data_array = np.array(block_data)
            na_count += np.count_nonzero(np.isnan(block_data_array))

            assert len(block_row_header) == block_data_array.shape[0]
            assert data.shape[1] == block_data_array.shape[1]

            data[row_index:block_end, :] = block_data_array

            row_index = block_end

        # lastly write the labels along the two axes
        str_dt = h5py.special_dtype(vlen=bytes)

        dim_0 = file_hdf5.create_dataset("dim_0", (len(row_header),), dtype=str_dt)
        dim_0[:] = row_header
        dim_0.attrs['name'] = "row_axis"

        dim_1 = file_hdf5.create_dataset("dim_1", (len(col_header),), dtype=str_dt)
        dim_1[:] = col_header
        dim_1.attrs['name'] = "col_axis"

        if description_column is not None:
            assert len(description_column) == len(row_header)
            dim_0 = file_hdf5.create_dataset("gct_description", (len(description_column),), dtype=str_dt)
            dim_0[:] = description_column
            dim_0.attrs['name'] = "row_description"

        assert len(row_header) == row_count, "Row header length did not match expected row count"
    return na_count, row_header


def _pack_into_matrix(rows):
    data = np.empty((len(rows), len(rows[0])), 'd')
    data[:] = np.nan

    for row_i, row in enumerate(rows):
        for col_i, value in enumerate(row):
            if value == "NA" or value == "":
                parsed_value = np.nan
            else:
                parsed_value = float(value)
            data[row_i, col_i] = parsed_value
    return data

def _read_rows_in_chunks(first_line, progress, dst_hdf5_file, col_header, r, rows_per_chunk, dialect):
    row_header = []
    rows = []
    line = first_line
    for row in r:
        if line % 250 == 0:
            message = "Conversion in progress, line {}".format(line)
            progress.progress(message, dst_hdf5_file, line)

        line += 1
        row_header.append(row[0])
        data_row = row[1:]
        if len(data_row) == 0:
            message = """On line {}: found no data, only row header label {}.  Did you choose the right delimiter
                for this file? (Currently using {})""".format(line, repr(row[0]), repr(dialect.delimiter))
            progress.failed(message, dst_hdf5_file)
            raise Exception(message)

        if len(data_row) != len(col_header):
            message = "On line %d: Expected %d columns, but found %d columns." % (
                line, len(col_header), len(data_row))
            if line == 2 and (len(col_header) - 1) == len(data_row):
                message += "  This looks like you may be missing R-style row and column headers from your file, or you were loading a table, and not a numerical matrix."
            progress.failed(message, dst_hdf5_file)
            raise Exception(message)

        rows.append(data_row)

        if len(rows) >= rows_per_chunk:
            yield row_header, _pack_into_matrix(rows)
            rows = []
            row_header = []
            first_line = line

    if len(rows) > 0:
        yield row_header, _pack_into_matrix(rows)

