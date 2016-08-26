import Crypto.Hash.SHA256 as SHA256
import Crypto.PublicKey.RSA as RSA
import Crypto.Signature.PKCS1_v1_5 as PKCS1_v1_5
import requests

GCS_API_ENDPOINT = 'https://storage.googleapis.com'

class GCSSigner:
    def __init__(self, key, client_id, expiration_delay=datetime.timedelta(days=1)):
        self.key = key
        self.client_id = client_id

    def _sign(self, plaintext):
        shahash = SHA256.new(plaintext)
        signer = PKCS1_v1_5.new(self.key)
        signature_bytes = signer.sign(shahash)
        return base64.b64encode(signature_bytes)

    def _format_signature_string(self, verb, path, content_md5, content_type, expiration_int):
        return "\n".join([verb, content_md5, content_type, expiration_int, path])
    
    def _format_url(self, verb, path, content_type='', content_md5=''):
        expiration_time = (datetime.datetime.now() + self.expiration_delay)
        expiration_int = int(time.mktime(expiration_time.timetuple()))
        signature_string = self._format_signature_string(verb, path, content_md5, content_type)
        signature_signed = self._sign(signature_string)
        
        query_params = dict(GoogleAccessId=self.client_id_email, 
            Expires=str(expiration_int),
            Signature=signature_signed)

        return (GCS_API_ENDPOINT + path, query_params)

    def get_upload_url(self, bucket, path, content_type):
        return _format_url("PUT", "/{}/{}".format(bucket, path))
                