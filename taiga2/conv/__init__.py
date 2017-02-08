from taiga2.conv.imp import csv_to_hdf5, tsv_to_hdf5
from taiga2.conv.exp import hdf5_to_rds, hdf5_to_csv

from taiga2.conv import columnar

def csv_to_columnar(progress, src, dst):
    return columnar.convert_csv_to_tabular(src, dst, ",")

# These three must all have the same signature: ( input_file, temp_file_generator: "() -> str" ) -> list of files
from taiga2.conv.columnar import columnar_to_rds

def columnar_to_csv(progress, src, temp_file_generator):
    dst = temp_file_generator()
    columnar.convert_tabular_to_csv(src, dst, ",")
    return [dst]


CSV_FORMAT = "csv"
RAW_FORMAT = "raw"
RDS_FORMAT = "rds"
HDF5_FORMAT = "hdf5"
COLUMNAR_FORMAT = "columnar"