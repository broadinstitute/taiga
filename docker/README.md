# Deploying Taiga as a docker container

- Run `build.sh` outside of taiga/ to tar the code and build the docker image
- Run `deploy.sh` to push the image to Amazon Registry Container (be careful to change the url of the repository)
- Go on your server to pull the image
- Execute the command `docker run -p 8888:8080 -t taiga`
