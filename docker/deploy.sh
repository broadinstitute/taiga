#!/usr/bin/env bash

docker_login=`aws ecr get-login --region us-east-1`
${docker_login}
docker tag taiga:latest 784167841278.dkr.ecr.us-east-1.amazonaws.com/taiga:latest
docker push 784167841278.dkr.ecr.us-east-1.amazonaws.com/taiga:latest