import datetime

#<editor-fold desc="MonkeyS3">
class MonkeyS3:
    def __init__(self):
        self.buckets = {}
        self.Bucket = MonkeyBucket(self)

    def Object(self, bucket_name, key):
        bucket = self.buckets[bucket_name]
        obj = bucket.objects[key]
        return obj


class MonkeyBucket:
    def __init__(self, s3):
        self.s3 = s3
        self.name = None
        self.objects = {}

    def create(self, name):
        self.name = name
        self.s3.buckets[self.name] = self
        return self

    def put_object(self, Key=None, Body=None):
        new_object = MonkeyS3Object(self, Key)
        new_object.upload_fileobj(Body)
        self.objects[new_object.key] = new_object
        return new_object

    def __call__(self, name):
        return self


class MonkeyS3Object:
    def __init__(self, bucket, key):
        self.bucket = bucket
        self.key = key
        self.prefix = '/tmp/'
        self.full_path = self.prefix + self.key

    def download_fileobj(self, data):
        with open(self.full_path, 'rb') as f:
            data.write(f.read())

    def upload_fileobj(self, data):
        with open(self.full_path, 'w+b') as f:
            f.write(data.read())

    def upload_file(self, path):
        with open(path, 'r') as data:
            with open(self.full_path) as f:
                f.write(data.read())
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
