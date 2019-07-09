#!/usr/bin/env bash
set -exv

REPO_URL=us.gcr.io/cds-docker-containers/taiga

cat travis/travis-docker-push-account.json | docker login -u _json_key --password-stdin https://us.gcr.io
docker tag taiga:latest ${REPO_URI}
docker push ${REPO_URI}