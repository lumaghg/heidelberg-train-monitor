#!/bin/bash

# execute every full minute

source /home/robin/Documents/github/rnv-train-monitor/myenv/bin/activate

cd /home/robin/Documents/github/rnv-train-monitor/src/rnv

sudo python ./rnv_compute_animationcodes.py
