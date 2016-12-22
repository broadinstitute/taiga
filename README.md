# Taiga 2

Web application to store and retrieve immutable data in a folder organized way.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

See deployment for notes on how to deploy the project on a live system (Coming soon).

## Prerequisites
Taiga 2 is built on the following stack:

- TinyDB
- Flask
- Celery/Redis
- Swagger
- React
- TypeScript
 
- Webpack
- Yarn
- Node/NPM

Please ensure you have installed these tools before proceeding to the next chapter.

## Installing

Starting the project is not yet straightforward, but will be in the near future:
 
1. Clone this repository to your machine:
 
        `git clone https://rmarenco@stash.broadinstitute.org/scm/cpds/taiga.git`

2. Checkout the Taiga 2 branch:

        `git checkout taiga2-prototype`

3. Install all the dependencies:

        `python setup.py develop`
        `yarn install`
        `cd frontend/ && yarn install && cd ..`

4. (Hopefully temporary) Replace, in frontend/@types/react-dropzone/index.d.ts the `export default Dropzone` by `export = Dropzone`
5. Configure the application as you need (AWS credentials, hostname/port and so on), in settings.cfg:

        `cp settings.cfg.sample settings.cfg && vim settings.cfg`

6. Open 4 terminal windows to launch Webpack, Taiga 2, Celery and Redis processes: 

    a. In the root folder:

        `webpack --progress --colors --watch`

    b. In your redis folder, with your redis configuration file redis.conf:

        `redis-server <redis.conf>`

    c. In the taiga2 folder:

        `taiga2 test.json`
        
        `celery -A taiga2 worker -l info -E`
        
7. Congratulations! You can now access to Taiga 2 through your browser at:

        `http://localhost:8080`


## Running the tests

Coming soon

## Deployment

Coming soon

## Contributing

Feel free to make a contribution and then submit a Pull Request (smile)

## Versioning

We use Git for versioning! If you don't know how to use it, we strongly recommend doing this tutorial.

## Authors

- Philip Montgomery - Initial work + advising on the current development
- Remi Marenco - Prototype + current development

## License

This project is licensed under the Apache License - see the LICENSE file for details.

## Acknowledgments

- Cancer Data Science