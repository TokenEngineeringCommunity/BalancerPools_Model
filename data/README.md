# How to use the new balancerpool.py script

BalancerAMM_Model Version 1.0 allows to query Balancer Pool transactions via Blockchain-ETL/GoogleCloud. In order to plug historical on-chain transaction data to the cadCAD model please take the following steps:

1. You [need credentials](https://cloud.google.com/docs/authentication/getting-started) to access GoogleCloud, create a user, respective service account, create your key, and store it for example at "/home/user/Downloads/my-key.json"
2. `pip install -r pulldata_requirements.txt` to install all packages required to work with Ethereum-Balancer datasets
3. `export GOOGLE_APPLICATION_CREDENTIALS="/home/user/Downloads/my-key.json"` will define the path to your GoogleCloud key created in step 1, valid for your current shell session
4. `python3 pulldata.py 0x0d88b55317516b84e78fbba7cde3f910d5686901` will download the data of any pool address you choose from Bigquery and save it in a directory 
5. `python3 pulldata.py 0x0d88b55317516b84e78fbba7cde3f910d5686901` (run a second time) detects then that the directory exists and will generate `actions.json` out of it for future use in this cadCAD model
