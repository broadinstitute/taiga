#!/usr/bin/env bash
set -ev
tar --exclude='dist' --exclude='*/taiga.tar.gz' --exclude='.idea' --exclude='node_modules' --exclude='frontend/node_modules' --exclude='.git' -zcvf docker/taiga.tar.gz *
docker build -t taiga:latest docker/