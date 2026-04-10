#!/usr/bin/env bash
set -evx

IMAGE_TAG="$1"

docker build -t ${IMAGE_TAG} .
