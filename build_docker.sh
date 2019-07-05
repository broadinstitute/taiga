#!/usr/bin/env bash
set -evx

# TODO: Need to see how to tar from travis/
tar --exclude='dist' --exclude='*/taiga.tar.gz' \
--exclude='.idea' --exclude='node_modules' --exclude='frontend/node_modules' --exclude='.git' \
--exclude='*.pyc' -zcvf docker/taiga.tar.gz *
docker build -t taiga:latest docker/

# TODO: We are missing multiple steps:
# - Retrieve the settings.cfg or create it in the VM?
