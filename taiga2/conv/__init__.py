from taiga2.conv.imp import csv_to_hdf5, tsv_to_hdf5

from taiga2.conv import columnar
from taiga2.conv.columnar import columnar_to_rds

def columnar_to_csv(progress, src, dst):
    return columnar.convert_tabular_to_csv(src, dst, ",")

def csv_to_columnar(progress, src, dst):
    return columnar.convert_csv_to_tabular(src, dst, ",")

CSV_FORMAT = "csv"
RAW_FORMAT = "raw"
RDS_FORMAT = "rds"
HDF5_FORMAT = "hdf5"
COLUMNAR_FORMAT = "columnar"