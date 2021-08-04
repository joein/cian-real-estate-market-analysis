#!/bin/bash
set -e

docker build -t justjoinme/cian-real-estate-market-analysis-test:latest -f DockerfileTest .
docker run -it justjoinme/cian-real-estate-market-analysis-test:latest
docker build justjoinme/cian-real-estate-market-analysis:latest -f Dockerfile .




