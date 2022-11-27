#!/bin/bash

sudo apt update
sudo apt install ffmpeg -y

pip install pipenv
pipenv install && pipenv install --dev
