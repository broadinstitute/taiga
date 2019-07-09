#!/bin/bash
set -xe

docker build . -t us.gcr.io/cds-docker-containers/taiga-base:v1
docker push us.gcr.io/cds-docker-containers/taiga-base:v1
