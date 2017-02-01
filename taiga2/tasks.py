from taiga2.models import generate_permaname
from taiga2.aws import aws
from celery import Celery
from taiga2 import conversion

celery = Celery("taiga2")
#Celery("taiga2", include=['taiga2.tasks'])

@celery.task
def print_config():
    import flask
    config = flask.current_app.config

@celery.task(bind=True)
def background_process_new_upload_session_file(self, S3UploadedFileMetadata):
    import os

    # TODO: Rename this as it is confusing
    datafile = S3UploadedFileMetadata
    # TODO: The permaname should not be generated here, but directly fetch from key
    file_name = datafile['key']
    # TODO: Would be better to have a permaname generation from the domain controller instead
    permaname = generate_permaname(datafile['key'])
    file_type = datafile['filetype']

    
    # If we receive a raw file, we don't need to do anything
    from taiga2.models import DataFile
    # TODO: Instead of comparing two strings, we could also use DataFileType(file_type) and compare the result, or catch the exception
    if file_type == DataFile.DataFileType.Raw.value:
        message = "Received {}".format(file_name)
        self.update_state(state='PROGRESS',
                          meta={'current': 0, 'total': '0',
                                'message': message, 'fileName': file_name})
    elif file_type == DataFile.DataFileType.Columnar.value:
        # TODO: Think about the access of Celery to S3 directly
        s3 = aws.s3
        object = s3.Object(datafile['bucket'], datafile['key'])
        temp_raw_tcsv_file_path = '/tmp/taiga2/' + permaname
        os.makedirs(os.path.dirname(temp_raw_tcsv_file_path), exist_ok=True)

        with open(temp_raw_tcsv_file_path, 'w+b') as data:
            message = "Downloading the file from S3"
            self.update_state(state='PROGRESS',
                              meta={'current': 0, 'total': '0',
                                        'message': message, 'fileName': file_name})
            object.download_fileobj(data)

        temp_hdf5_tcsv_file_path = conversion.tcsv_to_hdf5(self, temp_raw_tcsv_file_path, file_name)  

        # Upload the hdf5
        message = "Uploading the HDF5 to S3"
        self.update_state(state='PROGRESS',
                          meta={'current': 0, 'total': '0',
                                    'message': message, 'fileName': file_name})

        with open(temp_hdf5_tcsv_file_path, 'rb') as data:
            object.upload_fileobj(data)
    elif file_type == DataFile.DataFileType.HDF5.value:
        message = "HDF5 conversion is not implemented yet (filename {})".format(file_name)
        self.update_state(state='FAILURE',
                          meta={'current': 0, 'total': '0',
                                'message': message, 'fileName': file_name})
        raise Exception(message)
    else:
        message = "The file type {} is not known for {}".format(file_type, file_name)
        self.update_state(state='FAILURE',
                          meta={'current': 0, 'total': '0',
                                'message': message, 'fileName': file_name})
        raise Exception(message)


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
