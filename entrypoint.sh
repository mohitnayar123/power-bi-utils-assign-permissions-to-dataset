#!/bin/sh
pip install --upgrade pip
pip install requests
pip install pyyaml
pip install os
pip install logging
pip install argparse
pip install pathlib

python /scripts/python/assign_group.py $1 $2 "$3" $4
