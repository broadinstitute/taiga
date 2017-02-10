#!/usr/bin/env bash
set -ev
docker_image=784167841278.dkr.ecr.us-east-1.amazonaws.com/taiga:latest
docker_login=`aws ecr get-login --region us-east-1`
${docker_login}
docker tag taiga:latest ${docker_image}
docker push ${docker_image}
ssh ubuntu@depmap.org  "${docker_login} && docker pull ${docker_image} && docker run -d -p 8888:8080 ${docker_image}"