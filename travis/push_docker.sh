#!/usr/bin/env bash
set -exv

REPO_URI=us.gcr.io/cds-docker-containers/taiga

docker tag taiga:latest ${REPO_URI}
docker push ${REPO_URI}