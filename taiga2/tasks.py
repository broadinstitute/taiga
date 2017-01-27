import taiga2.controllers.models_controller as models_controller
from celery import shared_task

@shared_task(bind=True)
def background_process_new_datafile(self, S3UploadedFileMetadata, sid, upload_session_file_id):
    import boto3
    import os

    # TODO: Rename this as it is confusing
    datafile = S3UploadedFileMetadata
    # TODO: The permaname should not be generated here, but directly fetch from key
    file_name = datafile['key']
    permaname = models_controller.generate_permaname(datafile['key'])

    # TODO: Think about the access of Celery to S3 directly
    s3 = boto3.resource('s3')
    object = s3.Object(datafile['bucket'], datafile['key'])
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

# @shared_task(bind=True)
# def print_hello(self):
#     print("called")
#     print("self=%s"%self)

