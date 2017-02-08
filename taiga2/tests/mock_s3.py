import copy
import datetime
import os
import io
import tempfile
import re

#<editor-fold desc="MonkeyS3">
class MockS3:
    def __init__(self, tmpdir):
        self.file_per_key = {}
        self.tmpdir = tmpdir

    def _get_unique_filename(self):
        fd = tempfile.NamedTemporaryFile(dir=self.tmpdir, delete=False)
        fd.close()
        return fd.name

    def Bucket(self, bucket_name):
        return MockBucket(self, bucket_name)

    def Object(self, bucket_name, key):
        bucket = self.Bucket(bucket_name)
        return MockS3Object(bucket, key)

    def generate_presigned_url(self, ClientMethod, Params):
        assert ClientMethod=='get_object'
        return "s3://"+Params["Bucket"]+"/"+Params["Key"]+"?signed"



class MockBucket:
    def __init__(self, s3, name):
        self.s3 = s3
        self.name = name

    def create(self):
        return self

    # TODO: I am adding back the capitalized arguments because this is how it is done in the Boto3 doc: http://boto3.readthedocs.io/en/latest/reference/services/s3.html#S3.Bucket.put_object
    def put_object(self, Key, Body):
        new_object = MockS3Object(self, Key)
        new_object.upload_fileobj(Body)
        return new_object

    def copy(self, copy_source, key):
        bucket_source_name = copy_source['Bucket']
        key_source_name = copy_source['Key']

        path_source = self.s3.file_per_key[(bucket_source_name, key_source_name)]
        # obj_source = self.s3.buckets[bucket_source_name].objects[key_source_name]

        with open(path_source, "rb") as data_copy_source:
            self.put_object(key, data_copy_source)

    def __call__(self, name):
        return self


class MockS3Object:
    def __init__(self, bucket, key):
        self.bucket = bucket
        self.key = key
        self.prefix = '/tmp/'

        os.makedirs(os.path.dirname(self.full_path), exist_ok=True)

    @property
    def full_path(self):
        return self.prefix + self.key

    def download_fileobj(self, writer):
        full_path = self.bucket.s3.file_per_key[(self.bucket.name, self.key)]

        with open(full_path, 'rb') as f:
            writer.write(f.read())

    def upload_fileobj(self, fileobj):
        full_path = self.bucket.s3._get_unique_filename()

        with open(full_path, 'w+b') as f:
            f.write(fileobj.read())

        self.bucket.s3.file_per_key[(self.bucket.name, self.key)] = full_path

    def upload_file(self, path):
        with open(path, 'rb') as data:
            self.upload_fileobj(data)

    def upload_bytes(self, b):
        """Not a real boto3 method.  Just convience for testing"""
        assert isinstance(b, bytes)
        self.upload_fileobj(io.BytesIO(b))

    def download_as_bytes(self):
        """Not a real boto3 method.  Just convience for testing"""
        full_path = self.bucket.s3.file_per_key[(self.bucket.name, self.key)]

        with open(full_path, 'rb') as f:
            return f.read()

#</editor-fold>

class MockS3Client:
    def generate_presigned_url(self, ClientMethod, Params):
        return "https://mocks3/{}/{}?signed=Y".format(Params["Bucket"], Params["Key"])

def parse_presigned_url(url):
    g = re.match("https://mocks3/([^/]+)/([^?]+)\\?signed=Y", url)
    return g.group(1), g.group(2)


#<editor-fold desc="MonkeySTS">
class MockSTS:
    def get_session_token(self, *args, **kwargs):
        expiration_seconds = kwargs.get('DurationSeconds', 900)
        datetime_expiration = datetime.datetime.now() + datetime.timedelta(0, expiration_seconds)
        dict_credentials = {
            'Credentials': {
                'AccessKeyId': 'AccessKeyId',
                'Expiration': datetime_expiration.timestamp(),
                'SecretAccessKey': 'SecretAccessKey',
                'SessionToken': 'SessionToken'
            }
        }
        return dict_credentials
#</editor-fold>
