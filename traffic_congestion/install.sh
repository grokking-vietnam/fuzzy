#!/bin/sh

poetry install --no-root
poetry run pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu116
