#!/bin/sh

# 使用方法：./testscript.sh
rm -rf trace.csv
rm -rf testgoogle.py
wget http://192.168.1.102/download/trace.csv
wget http://192.168.1.102/download/testgoogle.py
python3 testgoogle.py