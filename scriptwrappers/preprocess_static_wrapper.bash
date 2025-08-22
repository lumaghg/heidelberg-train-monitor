#!/bin/bash

# execute 20s after startup and at 0:05 am

cd /home/robin/Documents/github/heidelberg-train-monitor/src/rnv
sudo /home/robin/Documents/github/heidelberg-train-monitor/venv/bin/python ./rnv_preprocess_static.py

cd /home/robin/Documents/github/heidelberg-train-monitor/src/db
sudo /home/robin/Documents/github/heidelberg-train-monitor/venv/bin/python ./db_preprocess_static.py

cd /home/robin/Documents/github/heidelberg-train-monitor/src/de
sudo /home/robin/Documents/github/heidelberg-train-monitor/venv/bin/python ./de_preprocess_static.py
