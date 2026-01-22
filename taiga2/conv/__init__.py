BYTES_PER_STR_OBJECT = 60
MAX_MB_PER_CHUNK = 50

# These three must all have the same signature: ( input_file, temp_file_generator: "() -> str" ) -> list of files
from taiga2.conv.columnar import read_column_definitions

from taiga2.conv.imp import csv_to_hdf5
from taiga2.conv.exp import hdf5_to_csv, hdf5_to_tsv, hdf5_to_gct

from taiga2.conv import columnar


def csv_to_columnar(progress, src, dst, encoding="iso-8859-1", **kwargs):
    return columnar.convert_csv_to_tabular(src, dst, ",", encoding, **kwargs)


def columnar_to_csv(progress, src, temp_file_generator, encoding="iso-8859-1"):
    dst = temp_file_generator()
    columnar.convert_tabular_to_csv(src, dst, ",", encoding)
    return [dst]


def columnar_to_tsv(progress, src, temp_file_generator, encoding="iso-8859-1"):
    dst = temp_file_generator()
    columnar.convert_tabular_to_csv(src, dst, "\t", encoding)
    return [dst]


# text formats
CSV_FORMAT = "csv"
TSV_FORMAT = "tsv"
GCT_FORMAT = "gct"

RAW_FORMAT = "raw"
COMPRESSED_FORMAT = "raw_test"

# Canonical format
HDF5_FORMAT = "hdf5"
COLUMNAR_FORMAT = "columnar"
