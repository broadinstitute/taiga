import math

class Progress:
    def __init__(self, celery_instance):
        self.celery_instance = celery_instance

    def failed(self, message, filename):
        self.celery_instance.update_state(state='FAILURE',
                                     meta={'current': 0, 'total': '0',
                                           'message': message, 'fileName': filename})

    def progress(self, message, filename, current=0):
        self.celery_instance.update_state(state='PROGRESS',
                                     meta={'current': current, 'total': '0',
                                           'message': message, 'fileName': filename})


def _to_string_with_nan_mask(x):
    if math.isnan(x):
        return "NA"
    else:
        return str(x)


