import math
import contextlib
import os
import tempfile


@contextlib.contextmanager
def make_temp_file_generator():
    filenames = []

    def temp_file_generator():
        fd = tempfile.NamedTemporaryFile(delete=False)
        filename = fd.name
        fd.close()
        filenames.append(filename)
        print("Returning new file", filename)
        return filename

    yield temp_file_generator

    for filename in filenames:
        os.unlink(filename)


class Progress:
    def __init__(self, celery_instance):
        self.celery_instance = celery_instance

    def failed(self, message, filename=None):
        self.celery_instance.update_state(state='FAILURE',
                                          meta={'current': 0, 'total': '0',
                                                'message': message, 'fileName': filename})

    def progress(self, message, filename=None, current=0):
        self.celery_instance.update_state(state='PROGRESS',
                                          meta={'current': current, 'total': '0',
                                                'message': message, 'fileName': filename})


def _to_string_with_nan_mask(x):
    if math.isnan(x):
        return "NA"
    else:
        return str(x)


r_escape_str = lambda x: '"' + x.replace("\"", "\\\"") + '"'


def shortened_list(l):
    if len(l) > 30:
        return ", ".join(l[:15]) + " ... " + ", ".join(l[15:])
    else:
        return ", ".join(l)


import hashlib

from collections import namedtuple

ImportResult = namedtuple("ImportResult", "sha256 short_summary long_summary")


def get_file_sha256(filename):
    hash = hashlib.sha256()
    with open(filename, "rb") as fd:
        while True:
            buffer = fd.read(1024 * 1024)
            if len(buffer) == 0:
                break
            hash.update(buffer)
    return hash.hexdigest()
