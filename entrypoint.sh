#!/bin/sh
pip install --upgrade pip
pip install requests
pip install pyyaml
pip install pathlib

python /scripts/python/assign_group.py --files "$1" --tenant_id "$2" --config "$3"
