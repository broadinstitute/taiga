#!/usr/bin/env bash
set -exv

openssl aes-256-cbc -k "$super_secret_password" -in travis/travis-docker-push-account.json.enc -out travis/travis-docker-push-account.json -d
cat travis/travis-docker-push-account.json | docker login -u _json_key --password-stdin https://us.gcr.io
