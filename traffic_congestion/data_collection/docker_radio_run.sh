#!/bin/bash

read -p 'Radio channel name: ' channel
read -p 'M3U8 URL: ' url

docker build -f Dockerfile.radio . --build-arg CHANNEL=$channel --build-arg M3U8_URL=$url -t $channel
docker run --detach -it --restart=always --name=$channel $channel:latest
sleep 2
docker logs $channel
