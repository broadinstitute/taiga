import enum

from taiga2.models import generate_permaname, DataFile
import taiga2.controllers.models_controller as mc
from taiga2.aws import aws
from celery import Celery
import taiga2.conv as conversion
from taiga2.conv.util import Progress

celery = Celery("taiga2")

@celery.task
def print_config():
    import flask
    config = flask.current_app.config


@celery.task(bind=True)
def background_process_new_upload_session_file(self, S3UploadedFileMetadata, converted_s3_key):
    import os

    # TODO: Rename this as it is confusing
    datafile = S3UploadedFileMetadata
    # TODO: The permaname should not be generated here, but directly fetch from key
    s3_upload_key = datafile['key']
    filename = datafile['filename']
    # TODO: Would be better to have a permaname generation from the domain controller instead
    permaname = generate_permaname(datafile['key'])
    file_type = datafile['filetype']

    bucket_name = datafile['bucket']

    s3 = aws.s3
    bucket = s3.Bucket(bucket_name)

    # If we receive a raw file, we don't need to do anything
    from taiga2.models import DataFile
    # TODO: Instead of comparing two strings, we could also use DataFileType(file_type) and compare the result, or catch the exception
    if file_type == DataFile.DataFileType.Raw.value:
        message = "Received {}".format(s3_upload_key)
        self.update_state(state='PROGRESS',
                          meta={'current': 0, 'total': '0',
                                'message': message, 's3Key': s3_upload_key})

        # Create a new converted object to upload
        message = "Uploading the {} to S3".format(DataFile.DataFileType(file_type))
        self.update_state(state='PROGRESS',
                          meta={'current': 0, 'total': '0',
                                'message': message, 's3Key': s3_upload_key})

        # We copy the file to 'convert/'
        copy_source = {
            'Bucket': bucket_name,
            'Key': s3_upload_key
        }
        converted_s3_object = bucket.copy(copy_source, converted_s3_key)

        return DataFile.DataFileType.Raw.value
    elif file_type == DataFile.DataFileType.Columnar.value:
        s3_object = s3.Object(bucket_name, s3_upload_key)
        temp_raw_tcsv_file_path = '/tmp/taiga2/' + permaname
        os.makedirs(os.path.dirname(temp_raw_tcsv_file_path), exist_ok=True)

        with open(temp_raw_tcsv_file_path, 'w+b') as data:
            message = "Downloading the file from S3"
            self.update_state(state='PROGRESS',
                              meta={'current': 0, 'total': '0',
                                        'message': message, 's3Key': s3_upload_key})
            s3_object.download_fileobj(data)

        temp_hdf5_tcsv_file_path = conversion.tcsv_to_hdf5(Progress(self), temp_raw_tcsv_file_path, s3_upload_key)

        # Create a new converted object to upload
        message = "Uploading the {} to S3".format(DataFile.DataFileType(file_type))
        self.update_state(state='PROGRESS',
                          meta={'current': 0, 'total': '0',
                                'message': message, 's3Key': s3_upload_key})

        with open(temp_hdf5_tcsv_file_path, 'rb') as data:
            converted_s3_object = bucket.put_object(Key=converted_s3_key, Body=data)

        return DataFile.DataFileType.HDF5.value
    elif file_type == DataFile.DataFileType.HDF5.value:
        message = "HDF5 conversion is not implemented yet"
        self.update_state(state='FAILURE',
                          meta={'current': 0, 'total': '0',
                                'message': message, 's3Key': s3_upload_key})
        raise Exception(message)
    else:
        message = "The file type {} is not known for {}".format(file_type, s3_upload_key)
        self.update_state(state='FAILURE',
                          meta={'current': 0, 'total': '0',
                                'message': message, 's3Key': s3_upload_key})
        raise Exception(message)


@celery.task
def update_session_file_converted_type(converted_type, upload_session_file_id):
    # TODO: Think about the implications of requiring the code of the app in celery => Would need to restart this service each time we change the code of the app
    # TODO: Handle the exception/error management here
    mc.update_session_file_converted_type(converted_type=converted_type,
                                          upload_session_file_id=upload_session_file_id)


# TODO: This is only for background_process_new_upload_session_file, how to get it generic for any Celery tasks?
def taskstatus(task_id):
    task = background_process_new_upload_session_file.AsyncResult(task_id)
    if task.state == 'PENDING':
        # job did not start yet
        response = {
            'id': task.id,
            'state': task.state,
            'message': 'Waiting in the task queue',
            'current': 0,
            'total': 1,
            's3Key': 'TODO'
        }
    elif task.state == 'SUCCESS':
        response = {
            'id': task.id,
            'state': task.state,
            'message': 'Task has successfully terminated',
            'current': 1,
            'total': 1,
            's3Key': 'TODO'
        }
    elif task.state != 'FAILURE':
        response = {
            'id': task.id,
            'state': task.state,
            'message': 'Failure :/' if not task.info else task.info.get('message', 'No message'),
            'current': 0 if not task.info else task.info.get('current', 0),
            'total': -1 if not task.info else task.info.get('total', -1),
            's3Key': 'TODO' if not task.info else task.info.get('s3Key', 'TODO')
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
            's3Key': 'TODO' if task.info else task.info.get('s3Key', 'TODO')
        }

    return response

import tempfile
import uuid
import flask

from taiga2.aws import parse_s3_url

def get_converter(src_format, dst_format):
    from taiga2.models import DataFile
    if src_format == DataFile.DataFileType.HDF5 and dst_format == conversion.CSV_FORMAT:
        return conversion.hdf5_to_tcsv
    if src_format == DataFile.DataFileType.Columnar and dst_format == conversion.CSV_FORMAT:
        return conversion.columnar_to_csv
    raise Exception("No conversion for {} to {}".format(src_format, dst_format))

def start_conversion_task(src_url, src_format, dst_format, cache_entry_id):
    from taiga2.controllers import models_controller

    dest_bucket = flask.current_app.config['S3_BUCKET']
    dest_key = flask.current_app.config['S3_PREFIX']+"/exported/"+str(uuid.uuid4().hex)

    s3 = aws.s3
    bucket, key = parse_s3_url(src_url)
    with tempfile.NamedTemporaryFile() as raw_t:
        with tempfile.NamedTemporaryFile() as conv_t:
            models_controller.update_conversion_cache_entry(cache_entry_id, "Downloading from S3")
            s3.Object(bucket, key).download_fileobj(raw_t)
            raw_t.flush()

            models_controller.update_conversion_cache_entry(cache_entry_id, "Running conversion")

            converter = get_converter(src_format, dst_format)
            converter(raw_t.name, conv_t.name)

            urls = ["s3://{}/{}".format(dest_bucket, dest_key)]

            models_controller.update_conversion_cache_entry(cache_entry_id, "Uploading converted file to S3")
            s3.Object(dest_bucket, dest_key).upload_fileobj(conv_t)

            models_controller.update_conversion_cache_entry(cache_entry_id, "Completed successfully", urls=urls)
