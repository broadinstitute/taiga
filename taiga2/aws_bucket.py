def config_bucket_cors(s3, bucket_name):
    bucket_cors = s3.BucketCors(bucket_name)
    bucket_cors.put(CORSConfiguration={
            'CORSRules': [
                {
                    'AllowedOrigins': [ '*' ],
                    'AllowedMethods': [ 'GET', 'POST', "PUT" ],
                    'ExposeHeaders': [ 'ETag' ],
                    'AllowedHeaders': [ "*" ]
                }
            ]
        })

