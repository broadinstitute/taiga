# Taiga 2

Web application to store and retrieve immutable data in a folder organized way.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

See deployment for notes on how to deploy the project on a live system (Coming soon).

## Prerequisites

- **Python 3.10** (required — the project pins `>=3.10,<3.11`)
- **Poetry** (dependency manager)
- **Node.js** and **Yarn** (for the React frontend)
- **Redis** (Celery broker and result backend)
- **Docker** (optional — only needed if you want to test file uploads via MiniStack)

### Stack overview

| Layer | Technologies |
|-------|-------------|
| Database | SQLite (local dev), PostgreSQL (production), SQLAlchemy |
| Backend/API | Python 3.10, Flask, Connexion (Swagger/OpenAPI), Celery/Redis |
| Object storage | AWS S3 (production), MiniStack (optional, local dev) |
| Frontend | React, TypeScript, Webpack, Yarn |

## Installing

1. Install Python dependencies:

        poetry install

2. Install frontend dependencies:

        cd react_frontend && yarn install && cd ..

3. Copy the sample settings file (if you don't already have one):

        cp settings.cfg.sample settings.cfg

4. Create the dev database:

        poetry run bash -c 'source setup_env.sh && flask recreate-dev-db'

## Running Locally

Start these four processes in separate terminal windows:

```bash
# Terminal 1 — Redis (skip if already running; check with `redis-cli ping`)
redis-server

# Terminal 2 — Webpack dev server (frontend hot reload)
poetry run bash -c 'source setup_env.sh && flask webpack'

# Terminal 3 — Flask app server
poetry run bash -c 'source setup_env.sh && flask run'

# Terminal 4 — Celery worker (async file conversion tasks)
poetry run bash -c 'source setup_env.sh && flask run-worker'
```

Open your browser to: **http://127.0.0.1:5000/taiga/**

You are automatically logged in as the seeded admin user (`admin@broadinstitute.org`) via the `DEFAULT_USER_EMAIL` setting.

Without S3 configured, you can browse/search the seeded data, create folders, and work with the UI. File uploads require either MiniStack or real AWS credentials (see below).

## Local S3 with MiniStack (Optional)

[MiniStack](https://github.com/Nahuel990/ministack) is a free, open-source AWS emulator that runs 33 AWS services (including S3 and STS) in a single Docker container. It lets you test the full upload pipeline locally without an AWS account.

### Setup

1. Start MiniStack:

        docker run -d --name ministack -p 4566:4566 nahuelnucera/ministack

2. Create the local S3 bucket (run once):

    ```bash
    python -c "import boto3; boto3.client('s3', endpoint_url='http://localhost:4566', aws_access_key_id='test', aws_secret_access_key='test').create_bucket(Bucket='taiga-dev')"
    ```

3. In `settings.cfg`, uncomment the MiniStack block (Option A) and comment out Option B:

    ```python
    S3_ENDPOINT_URL = 'http://localhost:4566'
    AWS_ACCESS_KEY_ID = 'test'
    AWS_SECRET_ACCESS_KEY = 'test'
    S3_BUCKET = 'taiga-dev'
    ```

4. Restart Flask and the Celery worker to pick up the new settings.

### Managing MiniStack

```bash
docker start ministack   # start (if previously stopped)
docker stop ministack    # stop
docker rm ministack      # remove entirely
```

### Switching back to no-S3 mode

Set `S3_ENDPOINT_URL = ''` and clear the AWS keys in `settings.cfg`. The app runs fine without S3 — you just can't upload files.

## Configuring AWS (Production)

We need two users: One IAM account (main) is used in general by the app to read/write to S3. The second (uploader) has it's rights delegated via STS on a short term basis. However, this user should
only have access to upload to a single location within S3.

Permissions for the main user:

```json
{
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

```json
{
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

```json
[
  {
    "AllowedOrigins": ["*"],
    "AllowedMethods": ["GET", "POST", "PUT"],
    "ExposeHeaders": ["ETag"],
    "AllowedHeaders": ["*"]
  }
]
```

**_Warning: Be careful to not override your existing configuration!_**

#### Configure Taiga to use your Bucket

1. Edit `settings.cfg` and set `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`
2. Set `S3_BUCKET` to the bucket created above
3. Remove `S3_ENDPOINT_URL` (or leave it empty) so the app connects to real AWS

## Adding user to admin group

```sql
INSERT INTO group_user_association (group_id, user_id) select 1, id FROM users WHERE name =
'pmontgom';
```

## Running the tests

Install rhdf5 R library => http://bioconductor.org/packages/release/bioc/html/rhdf5.html

`pytest` from the root

## Deployment to Production

Every push triggers the GitHub Actions workflow (`.github/workflows/build-docker.yaml`), which:

1. Builds the Docker image from the root `Dockerfile`
2. Runs `pytest` inside the image
3. Pushes to `us.gcr.io/cds-docker-containers/taiga:ga-build-<run_number>`
4. On `main`, also tags and pushes as `us.gcr.io/cds-docker-containers/taiga:latest`

Once the workflow completes, `ssh` into `ubuntu@cds.team`:

1. Pull the latest image: `bash GOOGLE_APPLICATION_CREDENTIALS=/etc/google/auth/docker-pull-creds.json docker pull us.gcr.io/cds-docker-containers/taiga`
2. Tag the image with `taiga-prod` and `taiga-staging`. For example: `GOOGLE_APPLICATION_CREDENTIALS=/etc/google/auth/docker-pull-creds.json docker tag us.gcr.io/cds-docker-containers/taiga:ga-build-68 us.gcr.io/cds-docker-containers/taiga:taiga-staging` and `GOOGLE_APPLICATION_CREDENTIALS=/etc/google/auth/docker-pull-creds.json docker tag us.gcr.io/cds-docker-containers/taiga:ga-build-68 us.gcr.io/cds-docker-containers/taiga:taiga-prod`
3. Restart the service: `sudo systemctl restart taiga`

If there's any problem, then you can look for information in the logs (stored at
`/var/log/taiga`) or ask journald for the output from the service (`journalctl -u taiga`).

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

- `TAIGA_SETTINGS_FILE=prod_settings.cfg ./flask db migrate`

Review the resulting generated migration. I've found I've had to re-order
tables to ensure fk references are created successfully. Before applying the
migration, take a snapshot of the current Taiga db.

Depending on your changes, you may be able to apply them without stopping the service and minimizing downtime. You can apply online changes **if** they are compatible with both the old and new versions of the code that will be deployed. In general changes that migrate data are not safe, but trivial changes like adding new nullable fields or new tables are safe. See "Applying online changes" for updating the DB without stopping the service.

### Applying "offline" changes

- (Stop the service)
- `ssh ubuntu@cds.team sudo systemctl stop taiga`
- (Apply changes to the DB)
- `TAIGA_SETTINGS_FILE=prod_settings.cfg ./flask db upgrade`
- (And then pull and start the new code)
- `ssh ubuntu@cds.team`
- `GOOGLE_APPLICATION_CREDENTIALS=/etc/google/auth/docker-pull-creds.json docker pull us.gcr.io/cds-docker-containers/taiga`
- `sudo systemctl start taiga`

### Applying "online" changes

- (Apply changes to the DB)
- `TAIGA_SETTINGS_FILE=prod_settings.cfg ./flask db upgrade`
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
