import datetime
import io
import tempfile

#<editor-fold desc="MonkeyS3">
class MonkeyS3:
    def __init__(self, tmpdir):
        self.file_per_key = {}
        self.tmpdir = tmpdir

    def _get_unique_filename(self):
        fd = tempfile.NamedTemporaryFile(dir=self.tmpdir, delete=False)
        fd.close()
        return fd.name

    def Bucket(self, bucket_name):
        return MonkeyBucket(self, bucket_name)

    def Object(self, bucket_name, key):
        bucket = self.Bucket(bucket_name)
        return MonkeyS3Object(bucket, key)

    def generate_presigned_url(self, ClientMethod, Params):
        assert ClientMethod=='get_object'
        return "s3://"+Params["Bucket"]+"/"+Params["Key"]+"?signed"
import re
def parse_presigned_url(url):
    g = re.match("s3://([^/]+)/([^?]+)\\?signed", url)
    return g.group(1), g.group(2)


class MonkeyBucket:
    def __init__(self, s3, name):
        self.s3 = s3
        self.name = name

    def create(self, name):
        self.name = name
        self.s3.buckets[self.name] = self
        return self

    def put_object(self, key, body):
        new_object = MonkeyS3Object(self, key)
        new_object.upload_fileobj(body)
        return new_object

    def __call__(self, name):
        return self


class MonkeyS3Object:
    def __init__(self, bucket, key):
        self.bucket = bucket
        self.key = key

    def download_fileobj(self, writer):
        full_path = self.bucket.s3.file_per_key[(self.bucket.name, self.key)]

        with open(full_path, 'rb') as f:
            writer.write(f.read())

    def upload_fileobj(self, data):
        full_path = self.bucket.s3._get_unique_filename()

        with open(full_path, 'w+b') as f:
            f.write(data.read())

        self.bucket.s3.file_per_key[(self.bucket.name, self.key)] = full_path

    def upload_file(self, path):
        with open(path, 'rb') as data:
            self.upload_fileobj(data)

    def upload_bytes(self, b):
        "Not a real boto3 method.  Just convience for testing"
        assert isinstance(b, bytes)
        self.upload_fileobj(io.BytesIO(b))

    def download_as_bytes(self):
        "Not a real boto3 method.  Just convience for testing"
        full_path = self.bucket.s3.file_per_key[(self.bucket.name, self.key)]

        with open(full_path, 'rb') as f:
            return f.read()

#</editor-fold>


#<editor-fold desc="MonkeySTS">
class MonkeySTS:
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
