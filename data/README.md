# How to use the new balancerpool.py script
1. You [need credentials](https://cloud.google.com/docs/authentication/getting-started) to access Google Bigquery.
2. `pip install -r requirements.txt`
3. `export GOOGLE_APPLICATION_CREDENTIALS="/home/user/Downloads/my-key.json"`
4.  `export NODE_URL="https://your_eth_node_url"`
5. `python3 balancerpool.py 0x0d88b55317516b84e78fbba7cde3f910d5686901` will download the data from Bigquery and save it in a directory for future use.
6. `python3 balancerpool.py 0x0d88b55317516b84e78fbba7cde3f910d5686901` detects that the directory exists and will generate `actions.json` out of it.
