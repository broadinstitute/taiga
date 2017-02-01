import csv

# Methods for converting internal formats (HDF5 or columnar) to all other formats (GCT, rds, tsv, csv)

def hdf5_to_tabular_csv(self, hdf5_path, destination_file, delimiter=",", dedup_headers=False):
    with self.hdf5fs.hdf5_open(hdf5_path) as f:
        fd_out = open(destination_file, "w")
        w = csv.writer(fd_out, delimiter=delimiter)

        data = f['data']

        row_header = list(f['dim_0'])
        col_header = list(f['dim_1'])

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

        w.writerow([""] + col_header)
        row_count = len(row_header)
        for i in range(row_count):
            row = data[i, :]
            w.writerow([row_header[i]] + [_to_string_with_nan_mask(x) for x in row])
        fd_out.close()

def columnar_to_tcsv(input_file, output_file, delimiter):
    columnar.convert_tabular_to_csv(columnar_path, output_file, delimiter)
