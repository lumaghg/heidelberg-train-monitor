#!/bin/bash

# start 10s after raspi startup

source /home/robin/Documents/github/rnv-train-monitor/myenv/bin/activate

cd /home/robin/Documents/github/rnv-train-monitor/src

sudo python ./display_statuscodes.py
