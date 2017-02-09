#!/usr/bin/env bash
set -ev

# This script needs AWS environment to be set
# REPO_URI needs also to be set as the repository URI
docker_login=`aws ecr get-login --region us-east-1`
${docker_login}
docker tag taiga:latest ${REPO_URI}
docker push ${REPO_URI}