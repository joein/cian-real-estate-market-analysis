#!/bin/bash
set -e

docker build -t $DOCKER_USERNAME/cian-real-estate-market-analysis-test:latest -f DockerfileTest .
docker run -it $DOCKER_USERNAME/cian-real-estate-market-analysis-test:latest

docker build -t $DOCKER_USERNAME/cian-real-estate-market-analysis:latest -f Dockerfile .
echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin
docker push $DOCKER_USERNAME/cian-real-estate-market-analysis:latest



