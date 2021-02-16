# How to use the new pulldata.py script
1. You [need credentials](https://cloud.google.com/docs/authentication/getting-started) to access Google Bigquery.
2. `pip install -r requirements.txt`
3. `export GOOGLE_APPLICATION_CREDENTIALS="/home/user/Downloads/my-key.json"`
4.  `export NODE_URL="https://your_eth_node_url"`
5. Create folder <pool_address>-prices (example: 0x0d88b55317516b84e78fbba7cde3f910d5686901-prices/), place tradingview csv exports there (file name has to include TOKENFIAT, example AAVEUSD.csv)
6. `python3 pulldata.py 0x0d88b55317516b84e78fbba7cde3f910d5686901 -f USD` will download the data from Bigquery and save it in a directory for future use, and generate `actions-prices.json`.

`python3 pulldata.py 0x0d88b55317516b84e78fbba7cde3f910d5686901` will generate a plain `actions.json` but this will not be usable by the simulation.
