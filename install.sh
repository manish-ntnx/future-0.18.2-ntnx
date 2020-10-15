#!/bin/bash

mkdir -p log
rm -rf build dist/*
python setup.py bdist_egg > "log/setup_py2_bdist_egg-`date "+%Y-%m-%d-%H-%M-%S"`.log"  2>&1
rm -rf build
python3 setup.py bdist_egg > "log/setup_py3_bdist_egg-`date "+%Y-%m-%d-%H-%M-%S"`.log"  2>&1
echo "Eggs:"
ls -lrt dist 
