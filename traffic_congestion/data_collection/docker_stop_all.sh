#!/bin/bash

docker rm -f $(docker ps | grep radio | awk '{print $1}')
docker rm -f $(docker ps | grep seaweedfs | awk '{print $1}')
