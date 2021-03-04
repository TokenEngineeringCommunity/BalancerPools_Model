# How to use the new pulldata.py script
1. You [need credentials](https://cloud.google.com/docs/authentication/getting-started) to access Google Bigquery.
2. `pip install -r requirements.txt`
3. `export GOOGLE_APPLICATION_CREDENTIALS="/home/user/Downloads/my-key.json"`
4.  `export NODE_URL="https://your_eth_node_url"`
5. `python3 pulldata.py 0x0d88b55317516b84e78fbba7cde3f910d5686901 tradingview -f USD` or `python3 pulldata.py 0x0d88b55317516b84e78fbba7cde3f910d5686901 coingecko -f USD` will download the data from Bigquery, the archive node, coingecko and save it in a directory for future use, and generate `actions-prices.json`.
