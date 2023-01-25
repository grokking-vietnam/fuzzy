#!/bin/bash

docker rm -f $(docker ps | grep radio | awk '{print $1}')
