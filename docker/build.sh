#!/bin/sh

# Should be run outside of the taiga directory
tar --exclude='dist' --exclude='.idea' --exclude='*/node_modules' --exclude='.git' -zcvf taiga/docker/taiga.tar.gz taiga
docker build -t taiga2:latest taiga/docker