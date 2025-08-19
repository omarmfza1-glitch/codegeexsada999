#!/bin/bash
set -e
apt-get update
apt-get install -y libsndfile1
pip install --no-cache-dir -r requirements.txt
