import pandas as pd
import argparse
import os
import json
from google.cloud import bigquery
from datetime import datetime
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json
parser = argparse.ArgumentParser(prog="balancerpool", description="Ask Google Bigquery about a particular Balancer pool. Remember to set GOOGLE_APPLICATION_CREDENTIALS from https://cloud.google.com/docs/authentication/getting-started")
parser.add_argument("pool_address")
args = parser.parse_args()

@dataclass_json
@dataclass
class Action:
    tx_type: str
    tx_hash: str
    datetime: str
    parameters: dict

def query(client, sql: str) -> pd.DataFrame:
    print("Querying", sql)
    result = (
        client.query(sql)
        .result()
        .to_dataframe()
    )
    return result

def save_queries(pool_address: str, event_type: str, df: pd.DataFrame):
    print("Saving to", pool_address)
    if not os.path.exists(args.pool_address):
        os.mkdir(pool_address)
    df.to_json("{}/{}.json".format(pool_address, event_type))

if not os.path.exists(args.pool_address):
    swap_sql = 'select * from blockchain-etl.ethereum_balancer.BPool_event_LOG_SWAP where contract_address="{}"'.format(args.pool_address)
    join_sql = 'select * from blockchain-etl.ethereum_balancer.BPool_event_LOG_JOIN where contract_address="{}"'.format(args.pool_address)
    exit_sql = 'select * from blockchain-etl.ethereum_balancer.BPool_event_LOG_EXIT where contract_address="{}"'.format(args.pool_address)

    client = bigquery.Client()
    swap_results = query(client, swap_sql)
    join_results = query(client, join_sql)
    exit_results = query(client, exit_sql)
    save_queries(args.pool_address, "swap", swap_results)
    save_queries(args.pool_address, "join", join_results)
    save_queries(args.pool_address, "exit", exit_results)

else:
    join_results = pd.read_json("{}/join.json".format(args.pool_address))
    swap_results = pd.read_json("{}/swap.json".format(args.pool_address))
    exit_results = pd.read_json("{}/exit.json".format(args.pool_address))

    join_results["type"]="join"
    swap_results["type"]="swap"
    exit_results["type"]="exit"
    all_results = join_results.append(swap_results, ignore_index=True).append(exit_results, ignore_index=True)
    grouped_by_tx = all_results.groupby("transaction_hash")

    actions = []
    print("df stuff")
    for txhash, events in grouped_by_tx:
        if len(events) > 1:
            events["type"] = events["type"] + "_swap"

        e = events.to_dict(orient='index')
        # {272: {'block_number': 11558369,...}, 276: {'block_number':...}}

        subactions = [e[i] for i in e.keys()]
        # [{'block_number': 11558...}, {'block_number': ....}]
        actions.append(Action(tx_type=subactions[0]["type"], tx_hash=txhash, datetime=datetime.fromtimestamp(subactions[0]["block_timestamp"]/1000).isoformat(sep=" "), parameters=subactions))

    print("sorting by timestamp")
    actions.sort(key=lambda action:action.datetime)
    actions_dict = [a.to_dict() for a in actions]

    actions_filename = args.pool_address + "-actions.json"
    print("saving to", actions_filename)
    with open(actions_filename, 'w') as f:
        json.dump(actions_dict, f, indent="\t")
