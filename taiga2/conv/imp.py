import csv
import numpy as np

# methods for converting external dataformats to internal types.

def tcsv_to_hdf5(progress, src_csv_file, dst_hdf5_file):
    with open(src_csv_file, 'r') as tcsv:
        dialect = csv.Sniffer().sniff(tcsv.read(1024*20))
        tcsv.seek(0)
        r = csv.reader(tcsv, dialect)
        col_header = next(r)

        # check to see, does the header line up with the number of columns in the row, or do we need to shift it by one?
        first_column = 1 if col_header[0] == '' else 0
        col_header = col_header[first_column:]

        # validate to make sure no other column headers are blank.  We should communicate this to the submitted, but
        # doing it as a hard assertion for the time being.
        for i, x in enumerate(col_header):
            if x == '':
                message = "Column name for column {} was blank".format(i + 1, )
                progress.failed(message, dst_hdf5_file)
                raise Exception(message)

        row_header = []
        rows = []
        line = 1
        for row_i, row in enumerate(r):
            if row_i % 250 == 0:
                message = "Conversion in progress, row {}".format(row_i)
                progress.progress(message, dst_hdf5_file, row_i)

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
                    message += "  This looks like you may be missing R-style row and column headers from your file."
                progress.failed(message, dst_hdf5_file)
                raise Exception(message)
            rows.append(data_row)

    data = np.empty((len(rows), len(rows[0])), 'd')
    data[:] = np.nan
    message = "Numpy object under creation and population"
    progress.progress(message, dst_hdf5_file, row_i)

    for row_i, row in enumerate(rows):
        for col_i, value in enumerate(row):
            if value == "NA" or value == "":
                parsed_value = np.nan
            else:
                parsed_value = float(value)
            data[row_i, col_i] = parsed_value

    message = "Writing the hdf5 matrix"
    progress.progress(message, dst_hdf5_file, row_i)

    _write_hdf5_matrix(dst_hdf5_file, data, 'row_axis', row_header, 'col_axis', col_header)

def _write_hdf5_matrix(dst_hdf5_file, data, row_axis, row_header, col_axis, col_header):
    import h5py

    with h5py.File(dst_hdf5_file, 'w') as file_hdf5:
        str_dt = h5py.special_dtype(vlen=bytes)

        file_hdf5['data'] = data
        file_hdf5['data'].attrs['id'] = '0'

        dim_0 = file_hdf5.create_dataset("dim_0", (len(row_header),), dtype=str_dt)
        dim_0[:] = row_header
        dim_0.attrs['name'] = row_axis

        dim_1 = file_hdf5.create_dataset("dim_1", (len(col_header),), dtype=str_dt)
        dim_1[:] = col_header
        dim_1.attrs['name'] = col_axis

from taiga2.conv import columnar

def tcsv_to_columnar(self, input_file, output_file, delimiter):
    columnar.convert_csv_to_tabular(input_file, output_file, delimiter)
