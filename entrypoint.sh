#!/bin/sh
pip install --upgrade pip
pip install requests
pip install pyyaml
pip install pandas
pip install os
pip install logging

python /scripts/python/upload_file.py $1 $2 "$3" $4
