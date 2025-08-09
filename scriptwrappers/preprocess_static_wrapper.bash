#!/bin/bash

# execute 20s after startup and at 0:05 am

source /home/robin/Documents/github/rnv-train-monitor/myenv/bin/activate

cd /home/robin/Documents/github/rnv-train-monitor/src/rnv

sudo python ./rnv_preprocess_static.py

