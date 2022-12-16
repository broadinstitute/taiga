#!/usr/bin/env bash
set -evx

IMAGE_TAG="$1"

# TODO: Need to see how to tar from travis/
#tar --exclude='dist' \
#--exclude='*/taiga.tar.gz' \
#--exclude='*.pyc' \
#--exclude='*~' \
#--exclude='.idea' --exclude='node_modules' --exclude='frontend/node_modules' --exclude='.git' -zcvf docker/taiga.tar.gz *
docker build -t ${IMAGE_TAG} .

# TODO: We are missing multiple steps:
# - Retrieve the settings.cfg or create it in the VM?
