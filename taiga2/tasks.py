import time

from taiga2.celery import celery
import taiga2.controllers.models_controller as models_controller
from taiga2.aws import aws

@celery.task(bind=True)
def tcsv_to_hdf5(self, S3UploadedFileMetadata):
    import csv
    import numpy as np
    import os

    datafile = S3UploadedFileMetadata
    # TODO: The permaname should not be generated here, but directly fetch from key
    file_name = datafile['key']
    permaname = models_controller.generate_permaname(datafile['key'])

    s3 = aws.s3
    object = s3.Object(datafile['bucket'], datafile['key'])
    temp_raw_tcsv_file_path = '/tmp/taiga2/'+permaname
    os.makedirs(os.path.dirname(temp_raw_tcsv_file_path), exist_ok=True)
    with open(temp_raw_tcsv_file_path, 'w+b') as data:
        message = "Downloading the file from S3"
        self.update_state(state='PROGRESS',
                          meta={'current': 0, 'total': '0',
                                'message': message, 'fileName': file_name})
        object.download_fileobj(data)

    with open(temp_raw_tcsv_file_path, 'r') as tcsv:
        dialect = csv.Sniffer().sniff(tcsv.read(1024))
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
                raise Exception("Column name for column %d was blank" % (i + 1,))

        row_header = []
        rows = []
        line = 1
        for row_i, row in enumerate(r):
            if row_i % 250 == 0:
                message = "Conversion in progress, row {}".format(row_i)
                self.update_state(state='PROGRESS',
                                  meta={'current': row_i, 'total': '0',
                                        'message': message, 'fileName': file_name})
            line += 1
            row_header.append(row[0])
            data_row = row[1:]
            if len(data_row) == 0:
                raise Exception(
                    "On line %d: found no data, only row header label %s.  Did you choose the right delimiter for this file? (Currently using %s)" % (
                        line, repr(row[0]), repr(dialect.delimiter)))
            if len(data_row) != len(col_header):
                msg = "On line %d: Expected %d columns, but found %d columns." % (
                    line, len(col_header), len(data_row))
                if line == 2 and (len(col_header) - 1) == len(data_row):
                    msg += "  This looks like you may be missing R-style row and column headers from your file."
                raise Exception(msg)
            rows.append(data_row)

    data = np.empty((len(rows), len(rows[0])), 'd')
    data[:] = np.nan
    message = "Numpy object under creation and population"
    self.update_state(state='PROGRESS',
                      meta={'current': row_i, 'total': '0',
                            'message': message, 'fileName': file_name})
    for row_i, row in enumerate(rows):
        for col_i, value in enumerate(row):
            if value == "NA" or value == "":
                parsed_value = np.nan
            else:
                parsed_value = float(value)
            data[row_i, col_i] = parsed_value
    temp_hdf5_tcsv_file_path = temp_raw_tcsv_file_path + '.hdf5'

    message = "Writing the hdf5 matrix"
    self.update_state(state='PROGRESS',
                      meta={'current': row_i, 'total': '0',
                            'message': message, 'fileName': file_name})
    succes = _write_hdf5_matrix(temp_hdf5_tcsv_file_path, data, 'row_axis', row_header, 'col_axis', col_header)
    if succes:
        print("Successfully created the HDF5")
        return temp_hdf5_tcsv_file_path
    else:
        print("Failed to create the HDF5")


def _write_hdf5_matrix(temp_hdf5_tcsv_file_path, data, row_axis, row_header, col_axis, col_header):
    import h5py

    with h5py.File(temp_hdf5_tcsv_file_path, 'w') as file_hdf5:
        str_dt = h5py.special_dtype(vlen=bytes)

        file_hdf5['data'] = data
        file_hdf5['data'].attrs['id'] = '0'

        dim_0 = file_hdf5.create_dataset("dim_0", (len(row_header),), dtype=str_dt)
        dim_0[:] = row_header
        dim_0.attrs['name'] = row_axis

        dim_1 = file_hdf5.create_dataset("dim_1", (len(col_header),), dtype=str_dt)
        dim_1[:] = col_header
        dim_1.attrs['name'] = col_axis

    # TODO: Find a better way to handle the errors which could appear along the way
    return True


# TODO: This is only for tcsv_to_hdf5, how to get it generic for any Celery tasks?
def taskstatus(task_id):
    task = tcsv_to_hdf5.AsyncResult(task_id)
    if task.state == 'PENDING':
        # job did not start yet
        response = {
            'id': task.id,
            'state': task.state,
            'message': 'Waiting in the task queue',
            'current': 0,
            'total': 1,
            'fileName': 'TODO'
        }
    elif task.state == 'SUCCESS':
        response = {
            'id': task.id,
            'state': task.state,
            'message': 'Task has successfully terminated',
            'current': 1,
            'total': 1,
            'fileName': 'TODO'
        }
    elif task.state != 'FAILURE':
        print("TASK object {}".format(task))
        print("TASK state {}".format(task.state))
        print("TASK INFO {}".format(task.info))
        response = {
            'id': task.id,
            'state': task.state,
            'message': task.info.get('message', 'No message'),
            'current': task.info.get('current', 0),
            'total': task.info.get('total', 1),
            'fileName': task.info.get('fileName', 'TODO')
        }
        if 'result' in task.info:
            response['result'] = task.info['result']
    else:
        response = {
            'id': task.id,
            'state': task.state,
            'message': task.info.get('message', 'No message'),
            'current': 1,
            'total': -1,
            'fileName': task.info.get('fileName', 'TODO')
        }

    return response


## Previously used to test Celery
# @frontend_app.celery.task
# def get_folder_async(folder_id):
#     """Celery task to fetch the folder from the Database"""
#     print("We are in Celery!")
#
#     db = persist.open_db('test.json')
#     print("Testing db: %s" % db.get_user('admin'))
#
#     folder = db.get_folder(folder_id)
#     if folder is None:
#         # TODO: replace flask.abort(404) by an error flag that we will catch in the caller
#         # flask.abort(404)
#         print("We did not find the folder_id %s" % folder_id)
#         return None
#
#     parents = [dict(name=f['name'], id=f['id']) for f in db.get_parent_folders(folder_id)]
#     entries = []
#     for e in folder['entries']:
#         if e['type'] == "folder":
#             f = db.get_folder(e['id'])
#             name = f['name']
#             creator_id = f['creator_id']
#             creation_date = f['creation_date']
#         elif e['type'] == "dataset":
#             d = db.get_dataset(e['id'])
#             name = d['name']
#             creator_id = d['creator_id']
#             creation_date = d['creation_date']
#         elif e['type'] == "dataset_version":
#             dv = db.get_dataset_version(e['id'])
#             print("dv=", dv)
#             d = db.get_dataset(dv['dataset_id'])
#             name = d['name']
#             creator_id = dv['creator_id']
#             creation_date = dv['creation_date']
#         else:
#             raise Exception("Unknown entry type: {}".format(e['type']))
#
#         creator = db.get_user(creator_id)
#         creator_name = creator['name']
#         entries.append(dict(
#             id=e['id'],
#             type=e['type'],
#             name=name,
#             creation_date=creation_date,
#             creator=dict(id=creator_id, name=creator_name)))
#
#     creator_id = folder['creator_id']
#     creator = db.get_user(creator_id)
#
#     response = dict(id=folder['id'],
#                     name=folder['name'],
#                     type=folder['type'],
#                     parents=parents,
#                     entries=entries,
#                     creator=dict(id=creator_id, name=creator['name']),
#                     creation_date=folder['creation_date'],
#                     acl=dict(default_permissions="owner", grants=[])
#                     )
#     print("get_folder stop", time.asctime())
#     return response
