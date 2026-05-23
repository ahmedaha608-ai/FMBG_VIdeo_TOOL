#!/bin/bash

echo "Starting FFmpeg Video Bot..."

python3 -m pip install --upgrade pip
pip3 install -r requirements.txt

python3 bot.py
