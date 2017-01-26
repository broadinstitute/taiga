import time
import tempfile

from taiga2.celery import celery
import taiga2.controllers.models_controller as models_controller

def get_s3_connection():
    import boto3
    boto3.resource('s3')

def parse_url_into_bucket_key(url):
    unimp()

@celery.task(bind=True)
def export_datafile(self, src_url, src_type, dst_format, cache_entry_id):
    import uuid

    s3 = get_s3_connection()
    bucket, key = parse_url_into_bucket_key(src_url)
    raw_object = s3.Object(bucket, key)

    #FIXME: What are valid values for these?
    assert src_type == "hdf5"
    assert dst_format == "csv"

    urls = []
    with tempfile.NamedTemporaryFile() as raw_fd:
        self.update_state(state='PROGRESS',
                          meta={'current': 0,
                                'total': '0',
                                'message': "Downloading from S3"})

        raw_object.download_file(raw_fd.name)

        self.update_state(state='PROGRESS',
                          meta={'current': 0,
                                'total': '0',
                                'message': "Converting"})

        with tempfile.NamedTemporaryFile() as converted_fd:
            tcsv_to_hdf5(self, raw_fd.name, converted_fd.name)

            # TODO: Prepend prefix from config onto key
            converted_key = "exported/"+str(uuid.uuid4().hex)

            converted_object = s3.Object(bucket, converted_key)
            self.update_state(state='PROGRESS',
                              meta={'current': 0,
                                    'total': '0',
                                    'message': "Uploading converted to S3"})

            converted_object.upload_file(converted_fd.name)

            urls.append("s3://{}/{}".format(bucket, converted_key))

        self.update_state(state='PROGRESS',
                          meta={'current': 0,
                                'total': '0',
                                'message': "Updating cache"})
        models_controller.conversion_complete(cache_entry_id, urls)

@celery.task(bind=True)
def background_process_new_datafile(self, S3UploadedFileMetadata, sid, upload_session_file_id):
    import os

    # TODO: Rename this as it is confusing
    datafile = S3UploadedFileMetadata
    # TODO: The permaname should not be generated here, but directly fetch from key
    file_name = datafile['key']
    permaname = models_controller.generate_permaname(datafile['key'])

    # TODO: Think about the access of Celery to S3 directly
    s3 = get_s3_connection()
    object = s3.Object(datafile['bucket'], datafile['key'])

    # FIXME: use tempfile.NamedTemporaryFile to ensure dest doesn't already exist and avoid hardcoded path
    temp_raw_tcsv_file_path = '/tmp/taiga2/' + permaname
    os.makedirs(os.path.dirname(temp_raw_tcsv_file_path), exist_ok=True)

    with open(temp_raw_tcsv_file_path, 'w+b') as data:
        message = "Downloading the file from S3"
        self.update_state(state='PROGRESS',
                          meta={'current': 0, 'total': '0',
                                'message': message, 'fileName': file_name})
        object.download_fileobj(data)

    temp_hdf5_tcsv_file_path = tcsv_to_hdf5(self, temp_raw_tcsv_file_path, file_name)

    # Upload the hdf5
    message = "Uploading the HDF5 to S3"
    self.update_state(state='PROGRESS',
                      meta={'current': 0, 'total': '0',
                            'message': message, 'fileName': file_name})

    with open(temp_hdf5_tcsv_file_path, 'rb') as data:
        object.upload_fileobj(data)


def tcsv_to_hdf5(celery_instance, temp_raw_tcsv_file_path, file_name):
    import csv
    import numpy as np

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
                message = "Column name for column {} was blank".format(i + 1, )
                celery_instance.update_state(state='FAILURE',
                                             meta={'current': 0, 'total': '0',
                                                   'message': message, 'fileName': file_name})
                raise Exception(message)

        row_header = []
        rows = []
        line = 1
        for row_i, row in enumerate(r):
            if row_i % 250 == 0:
                message = "Conversion in progress, row {}".format(row_i)
                celery_instance.update_state(state='PROGRESS',
                                             meta={'current': row_i, 'total': '0',
                                                   'message': message, 'fileName': file_name})
            line += 1
            row_header.append(row[0])
            data_row = row[1:]
            if len(data_row) == 0:
                message = """On line {}: found no data, only row header label {}.  Did you choose the right delimiter
                    for this file? (Currently using {})""".format(line, repr(row[0]), repr(dialect.delimiter))
                celery_instance.update_state(state='FAILURE',
                                             meta={'current': row_i, 'total': '0',
                                                   'message': message, 'fileName': file_name})
                raise Exception(message)
            if len(data_row) != len(col_header):
                message = "On line %d: Expected %d columns, but found %d columns." % (
                    line, len(col_header), len(data_row))
                if line == 2 and (len(col_header) - 1) == len(data_row):
                    message += "  This looks like you may be missing R-style row and column headers from your file."
                celery_instance.update_state(state='FAILURE',
                                             meta={'current': row_i, 'total': '0',
                                                   'message': message, 'fileName': file_name})
                raise Exception(message)
            rows.append(data_row)

    data = np.empty((len(rows), len(rows[0])), 'd')
    data[:] = np.nan
    message = "Numpy object under creation and population"
    celery_instance.update_state(state='PROGRESS',
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
    celery_instance.update_state(state='PROGRESS',
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


# TODO: This is only for background_process_new_datafile, how to get it generic for any Celery tasks?
def taskstatus(task_id):
    task = background_process_new_datafile.AsyncResult(task_id)
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
            'message': 'Failure :/' if not task.info else task.info.get('message', 'No message'),
            'current': 0 if not task.info else task.info.get('current', 0),
            'total': -1 if not task.info else task.info.get('total', -1),
            'fileName': 'TODO' if not task.info else task.info.get('fileName', 'TODO')
        }
        if 'result' in task.info:
            response['result'] = task.info['result']
    else:
        response = {
            'id': task.id,
            'state': task.state,
            'message': 'No Message' if task.info else task.info.get('message', 'No message'),
            'current': 1,
            'total': -1,
            'fileName': 'TODO' if task.info else task.info.get('fileName', 'TODO')
        }

    return response
