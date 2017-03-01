import os
from sqlalchemy import create_engine
engine = create_engine('sqlite:///'+os.path.abspath("metadata.sqlite3"), echo=True)
conn = engine.connect()

import csv
w_ds = open("datasets.csv", "wt")
w_ds_csv = csv.writer(w_ds)

w_dv = open("dataset_versions.csv", "wt")
w_dv_csv = csv.writer(w_dv)

def get_version_desc(permaname, version):
    print("fetching",permaname,version)
    return conn.execute("select v.description, u.email from data_version v join named_data nd on nd.named_data_id = v.named_data_id left outer join user u on u.user_id = v.created_by_user_id where nd.permaname = ? and v.version = ?", [permaname, version]).fetchone()

w_ds_csv.writerow(["name", "permaname", "description", "folder"])
w_dv_csv.writerow(["permaname", "id", "version", "type", "short_desc", "created_by", "created_timestamp", "s3_location"])

for name, permaname, is_public, latest_version in conn.execute("select name, permaname, is_public, latest_version from named_data").fetchall():
    description, created_by = get_version_desc(permaname, latest_version)
    if permaname.startswith("achilles"):
      folder = 'achilles'
    elif is_public:
      if permaname.startswith('ccle'):
        folder = 'ccle'
      else:
        folder = "public"
    else:
      if created_by is None and permaname.startswith('avana'):
        folder = 'achilles'
      else:
        folder = "home({})".format(created_by)

    w_ds_csv.writerow([name, permaname, description, folder])

    for dataset_id, version, hdf5_path, columnar_path, created_by, created_timestamp in conn.execute("select dataset_id, version, hdf5_path, columnar_path, u.email, created_timestamp from data_version v join named_data nd on nd.named_data_id = v.named_data_id join user u on u.user_id = v.created_by_user_id where nd.permaname = ? order by v.version", [permaname]).fetchall():
        if hdf5_path is not None:
            df_type = "hdf5"
            filename = dataset_id+".hdf5"
        else:
            df_type = "columnar"
            filename = dataset_id+".columnar"
        w_dv_csv.writerow([permaname, dataset_id, version, df_type, "short_desc", created_by, created_timestamp, "s3://taiga2/imported/"+filename])

w_ds.close()
w_dv.close()