#!/bin/bash

sudo apt update
sudo apt install ffmpeg -y # audio codec

pip install poetry
poetry config virtualenvs.in-project true

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
cd $script_dir && poetry install --no-root
