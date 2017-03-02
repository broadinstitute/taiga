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
- Python 3.5
- Flask
- Celery/Redis
- Swagger

### FrontEnd
- React
- TypeScript
- Webpack
- Yarn
- Node/NPM

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
  
***Warning: Be careful to not override your existing configuration!***

#### Configure Taiga to use your Bucket

***Coming soon***

And now please ensure you have installed these tools before proceeding to the next chapter.

## Installing

Starting the project is not yet straightforward, but will be in the near future:
 
1. Clone this repository to your machine:
 
        `git clone https://github.com/broadinstitute/taiga.git`

2. Checkout the Taiga 2 branch:

        `git checkout taiga2-prototype`

3. Install all the dependencies:

        `python setup.py develop`
        `yarn install`
        `cd frontend/ && yarn install && cd ..`

4. Configure the application as you need (AWS credentials, hostname/port and so on), in settings.cfg:

        `cp settings.cfg.sample settings.cfg && vim settings.cfg`

5. Create the database to have some data to work with:

        `python taiga2/create_test_db_sqlalchemy.py settings.cfg`

6. Open 4 terminal windows to launch Webpack, Taiga 2, Celery and Redis processes: 

    a. In the root folder:

        `npm run build --progress --colors --watch` or `./node_modules/.bin/webpack --progress --colors --watch`

    b. In your redis folder, with your redis configuration file redis.conf:

        `redis-server <redis.conf>`

    c. In the taiga2 folder:

        `taiga2 settings.cfg`

        `export TAIGA2_SETTINGS=settings.cfg ; celery -A taiga2 worker -l info -E`
        
7. Congratulations! You can now access to Taiga 2 through your browser at:

        `http://localhost:8080/taiga/`


## Running the tests

Install rhdf5 R library => http://bioconductor.org/packages/release/bioc/html/rhdf5.html

1. `cd taiga2/tests`
2. `pytest`

## Deployment

Coming soon

## Contributing

Feel free to make a contribution and then submit a Pull Request!

## Versioning

We use Git for versioning! If you don't know how to use it, we strongly recommend doing this tutorial.

## Authors

- Philip Montgomery - Initial work + advising on the current development
- Remi Marenco - Prototype + current development

## Acknowledgments

- Cancer Data Science
- Broad Institute