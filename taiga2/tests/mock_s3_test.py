from taiga2.tests.monkeys import MonkeyS3
import io

def test_mock_s3_basics(tmpdir):
    s3 = MonkeyS3(str(tmpdir))

    path = str(tmpdir)+"/download"

    s3.Bucket("bucket").put_object("key", io.BytesIO(b"abc"))
    with open(path, "wb") as w:
        s3.Object("bucket", "key").download_fileobj(w)

    open(path, "rb").read() == b"abc"



