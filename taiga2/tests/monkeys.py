import os


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

    def download_fileobj(self, data):
        with open(self.prefix+self.key, 'rb') as f:
            data.write(f.read())

    def upload_fileobj(self, data):
        with open(self.prefix + self.key, 'w+b') as f:
            f.write(data.read())

    def upload_file(self, path):
        with open(path, 'r') as data:
            with open(self.prefix+self.key) as f:
                f.write(data.read())
