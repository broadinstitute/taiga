from celery import Celery

import tempfile
import uuid
import flask
import logging

from taiga2.aws import aws
import taiga2.conv as conversion
from taiga2.conv.util import Progress
from taiga2.conv.util import make_temp_file_generator
from taiga2.controllers import models_controller
from taiga2.conv.imp import ImportResult

celery = Celery("taiga2")
log = logging.getLogger()

@celery.task
def print_config():
    import flask
    print(flask.current_app.config)

def _from_s3_convert_to_s3(progress, upload_session_file_id, s3_object, download_dest, converted_dest, converted_s3_object, converter):
    progress.progress("Downloading the file from S3")
    s3_object.download_fileobj(download_dest)
    download_dest.flush()

    import_result = converter(progress, download_dest.name, converted_dest.name)
    assert isinstance(import_result, ImportResult)
    models_controller.update_upload_session_file_summaries(upload_session_file_id, import_result.short_summary, import_result.long_summary)

    # Create a new converted object to upload
    progress.progress("Uploading to S3")
    converted_dest.seek(0)
    converted_s3_object.upload_fileobj(converted_dest)


@celery.task(bind=True)
def background_process_new_upload_session_file(self, upload_session_file_id, initial_s3_key, file_type, bucket_name, converted_s3_key):
    s3 = aws.s3
    progress = Progress(self)

    # If we receive a raw file, we don't need to do anything
    from taiga2.models import DataFile
    from taiga2 import models

    # TODO: Instead of comparing two strings, we could also use DataFileType(file_type) and compare the result, or catch the exception
    if file_type == models.InitialFileType.Raw.value:
        progress.progress("Received {}".format(initial_s3_key))

        # Create a new converted object to upload
        progress.progress("Uploading the {} to S3".format(DataFile.DataFileType(file_type)))

        # We copy the file to 'convert/'
        copy_source = {
            'Bucket': bucket_name,
            'Key': initial_s3_key
        }
        s3.Bucket(bucket_name).copy(copy_source, converted_s3_key)
    else:
        if file_type == models.InitialFileType.NumericMatrixCSV.value:
            converter = conversion.csv_to_hdf5
        elif file_type == models.InitialFileType.NumericMatrixTSV.value:
            converter = conversion.tsv_to_hdf5
        elif file_type == models.InitialFileType.TableCSV.value:
            converter = conversion.csv_to_columnar
        elif file_type == models.InitialFileType.TableTSV.value:
            converter = conversion.tsv_to_columnar
        elif file_type == models.InitialFileType.GCT.value:
            converter = conversion.gct_to_hdf5
        else:
            raise Exception("unimplemented: {}".format(file_type))

        s3_object = s3.Object(bucket_name, initial_s3_key)
        converted_s3_object = s3.Object(bucket_name, converted_s3_key)

        with tempfile.NamedTemporaryFile("w+b") as download_dest:
            with tempfile.NamedTemporaryFile("w+b") as converted_dest:
                _from_s3_convert_to_s3(progress, upload_session_file_id, s3_object, download_dest, converted_dest, converted_s3_object, converter)


# TODO: This is only for background_process_new_upload_session_file, how to get it generic for any Celery tasks?
def taskstatus(task_id):
    print("In task status of task_id {}".format(task_id))
    task = background_process_new_upload_session_file.AsyncResult(task_id)
    print("Task {}".format(task))
    print("The task is in state: {}".format(task.state))
    print("Task info is {}".format(task.info))
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
            'message': str(task.info),
            'current': 1,
            'total': -1,
            's3Key': 'TODO' if task.info else task.info.get('s3Key', 'TODO')
        }

    return response


def get_converter(src_format, dst_format):
    from taiga2.models import DataFile

    is_hdf5 = (src_format == str(DataFile.DataFileType.HDF5))
    is_columnar = str(DataFile.DataFileType.Columnar)

    if is_hdf5:
        if dst_format == conversion.CSV_FORMAT:
            return conversion.hdf5_to_csv
        elif dst_format == conversion.RDS_FORMAT:
            return conversion.hdf5_to_rds
        elif dst_format == conversion.TSV_FORMAT:
            return conversion.hdf5_to_tsv
        elif dst_format == conversion.GCT_FORMAT:
            return conversion.hdf5_to_gct
    elif is_columnar:
        if dst_format == conversion.CSV_FORMAT:
            return conversion.columnar_to_csv
        elif dst_format == conversion.TSV_FORMAT:
            return conversion.columnar_to_tsv
        elif dst_format == conversion.RDS_FORMAT:
            return conversion.columnar_to_rds

    raise Exception("No conversion for {} to {}".format(src_format, dst_format))

def _start_conversion_task(self, progress, bucket, key, src_format, dst_format, cache_entry_id):
    from taiga2.controllers import models_controller

    dest_bucket = flask.current_app.config['S3_BUCKET']

    s3 = aws.s3
    with tempfile.NamedTemporaryFile() as raw_t:
        with make_temp_file_generator() as temp_file_generator:
            models_controller.update_conversion_cache_entry(cache_entry_id, "Downloading from S3")
            s3.Object(bucket, key).download_fileobj(raw_t)
            raw_t.flush()

            models_controller.update_conversion_cache_entry(cache_entry_id, "Running conversion")

            converter = get_converter(src_format, dst_format)
            converted_files = converter(progress, raw_t.name, temp_file_generator)
            assert isinstance(converted_files, list)

            urls = []
            for converted_file in converted_files:
                dest_key = models_controller.EnumS3FolderPath.Export.value + str(uuid.uuid4().hex)
                urls.append("s3://{}/{}".format(dest_bucket, dest_key))

                models_controller.update_conversion_cache_entry(cache_entry_id, "Uploading converted file to S3")
                with open(converted_file, "rb") as converted_file_fd:
                    s3.Object(dest_bucket, dest_key).upload_fileobj(converted_file_fd)

        models_controller.update_conversion_cache_entry(cache_entry_id, "Completed successfully", urls=urls)


@celery.task(bind=True)
def start_conversion_task(self, bucket, key, src_format, dst_format, cache_entry_id):
    try:
        return _start_conversion_task(self, Progress(self), bucket, key, src_format, dst_format, cache_entry_id)
    except:
        models_controller.mark_conversion_cache_entry_as_failed(cache_entry_id)
        raise

