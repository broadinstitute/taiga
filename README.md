# Taiga 2

Web application to store and retrieve immutable data in a folder organized way.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

See deployment for notes on how to deploy the project on a live system (Coming soon).

## Prerequisites

Taiga 2 is built on the following stack:

### Database

- PostGre (to store the app information)
- Psycopg2
- SQLAlchemy
- Amazon S3 (to store the files)

### Backend/API

- Python 3.6
- Flask
- Celery/Redis
- Swagger

### FrontEnd

- React
- TypeScript
- Webpack
- Yarn

### Configuring AWS users

We need two users: One IAM account (main) is used in general by the app to read/write to S3. The second (uploader) has it's rights delegated via STS on a short term basis. However, this user should
only have access to upload to a single location within S3.

Permissions for the main user:

```{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "s3:*",
            "Resource": [
                "arn:aws:s3:::taiga2",
                "arn:aws:s3:::taiga2/*"
            ]
        }
    ]
}
```

Permissions for the "upload" user:

```{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "Stmt1482441362000",
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:HeadObject"
            ],
            "Resource": [
                "arn:aws:s3:::taiga2/upload/*"
            ]
        }
    ]
}
```

### Configuring S3

Because we are using S3 to store the files, we need to correctly configure the S3 service, and its buckets.

#### Create the store Bucket

Please follow [this tutorial](http://docs.aws.amazon.com/AmazonS3/latest/gsg/CreatingABucket.html)
from Amazon, on how to create a Bucket.

#### Configure the Bucket

We need now to be able to access to this Bucket programmatically,
and through [CORS](https://docs.aws.amazon.com/AmazonS3/latest/dev/cors.html#how-do-i-enable-cors) (Cross Origin Resource Sharing):

For our case, it is pretty simple:

1. Select your bucket in your [amazon S3 console](https://console.aws.amazon.com/s3/home?region=eu-west-1#)
2. Click on `Properties`
3. Click on the `Permissions` accordion
4. Click on `Edit CORS Configuration`
5. Paste the following configuration into the page that should appear (CORS Configuration Editor):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CORSConfiguration xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
  <CORSRule>
      <AllowedOrigin>*</AllowedOrigin>
      <AllowedMethod>GET</AllowedMethod>
      <AllowedMethod>POST</AllowedMethod>
      <AllowedMethod>PUT</AllowedMethod>
      <ExposeHeader>ETag</ExposeHeader>
      <AllowedHeader>*</AllowedHeader>
  </CORSRule>
</CORSConfiguration>
```

**_Warning: Be careful to not override your existing configuration!_**

#### Configure Taiga to use your Bucket

1. Copy `settings.cfg.sample` to `settings.cfg`
2. edit `settings.cfg` and set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY
3. also set S3_BUCKET to the bucket created above

## Installing

1.  Install all the dependencies:

        `sh install_prereqs.sh`

2.  Create a test database to have some data to work with:

        `./flask recreate-dev-db`

3.  Open 4 terminal windows to launch Webpack, Taiga 2, Celery and Redis processes:

    a. In terminal 1:

        `./flask webpack`

    b. In terminal 2:

        `redis-server`

    c. In terminal 3:

        `./flask run`

    d. In terminal 4:

        `./flask run-worker`

4.  Congratulations! You can now access to Taiga 2 through your browser at:

        `http://127.0.0.1:5000/taiga/`

## adding user to admin group

```
INSERT INTO group_user_association (group_id, user_id) select 1, id FROM users WHERE name =
'pmontgom';
```

## Running the tests

Install rhdf5 R library => http://bioconductor.org/packages/release/bioc/html/rhdf5.html

`pytest` from the root

## Deployment

Each commit on the taiga2 branch results in a Travis test/build. Travis, on test success, will build an image and push
it the Taiga image to GCP's container registry.

Once travis is complete, you can `ssh` into `ubuntu@cds.team` and execute:

- `GOOGLE_APPLICATION_CREDENTIALS=/etc/google/auth/docker-pull-creds.json docker pull us.gcr.io/cds-docker-containers/taiga`
- `sudo systemctl restart taiga`

If there's any problems you can look for information in the logs (stored at
/var/log/taiga) or asking journald for the output from the service ( `journalctl -u taiga` )

## Migrate the database

If your model change in SQLAlchemy and you already have a database you can't drop/recreate, you can use Alembic to
manage the migrations:

Example (but use accordingly to the state of you database, see [Alembic](http://alembic.zzzcomputing.com/en/latest/)):

(Note, this requires that you put the config for the production database at
../prod_settings.cfg so that it can find the current schema to compare
against. You can test against a snapshot of a database by going to the AWS
console and going to RDS, going to "Snapshots", and selecting "Restore
Snapshot". You can then place the new database's endpoing into
prod_settings.cfg.)

- `cd taiga2`
- `./manage.py -c ../prod_settings.cfg db migrate -m 'migration-msg'`

Review the resulting generated migration. I've found I've had to re-order
tables to ensure fk references are created successfully. Before applying the
migration, take a snapshot of the current Taiga db.

Depending on your changes, you may be able to apply them without stopping the service and minimizing downtime. You can apply online changes **if** they are compatible with both the old and new versions of the code that will be deployed. In general changes that migrate data are not safe, but trivial changes like adding new nullable fields or new tables are safe. See "Applying online changes" for updating the DB without stopping the service.

### Applying "offline" changes

- (Stop the service)
- `ssh ubuntu@cds.team sudo systemctl stop taiga`
- (Apply changes to the DB)
- `./manage.py -c ../prod_settings.cfg db upgrade`
- (And then pull and start the new code)
- `ssh ubuntu@cds.team`
- `GOOGLE_APPLICATION_CREDENTIALS=/etc/google/auth/docker-pull-creds.json docker pull us.gcr.io/cds-docker-containers/taiga`
- `sudo systemctl start taiga`

### Applying "online" changes

- (Apply changes to the DB)
- `./manage.py -c ../prod_settings.cfg db upgrade`
- (And then pull new code)
- `ssh ubuntu@cds.team`
- `GOOGLE_APPLICATION_CREDENTIALS=/etc/google/auth/docker-pull-creds.json docker pull us.gcr.io/cds-docker-containers/taiga`
- (start the service running the new code)
- `sudo systemctl restart taiga`

## Undeletion

Users are able to delete datasets through the UI. We do not allow the undeletion directly, but in some extreme cases,
we have a way of un-deleting:
The api has the deprecation endpoint (`/datasetVersion/{datasetVersionId}/deprecate`) which could be use to turn a
deleted dataset version to a deprecated one.

You can use a curl request, e.g `curl -d '{"deprecationReason":"notNeeded"}' -H "Content-Type: application/json" -X POST http://cds.team/taiga/api/datasetVersion/{datasetVersionId_here}/deprecate`

## Contributing

Feel free to make a contribution and then submit a Pull Request!

## Versioning

We use Git for versioning! If you don't know how to use it, we strongly recommend doing this tutorial.

## Authors

- Philip Montgomery - Initial work + advising on the current development + data processing
- Remi Marenco - Prototype + current development

## Acknowledgments

- Cancer Data Science
- Broad Institute
