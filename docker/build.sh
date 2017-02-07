#!/usr/bin/env bash

# Should be run outside of the taiga directory
tar --exclude='dist' --exclude='*/taiga.tar.gz' --exclude='.idea' --exclude='*/node_modules' --exclude='.git' -zcvf taiga/docker/taiga.tar.gz taiga
docker build -t taiga:latest taiga/docker