pip install --upgrade pip
pip install requests
pip install pyyaml
pip install pandas
pip install os
pip install logging

python /scripts/python/upload_file.py --tenant_id $1 --config_file $2 --folder $3 --files "$4"
