#!/bin/bash

read -p 'Radio channel name: ' channel
read -p 'M3U8 URL: ' url

docker build --build-arg CHANNEL=$channel --build-arg M3U8_URL=$url . -t $channel
docker run --detach -it --restart=always --name=voh_$channel $channel:latest
