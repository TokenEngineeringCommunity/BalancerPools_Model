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
    df.to_json("{}/{}.json".format(pool_address, event_type), orient="records")


def read_query_results(pool_address: str, event_type: str) -> pd.DataFrame:
    filename = "{}/{}.json".format(pool_address, event_type)
    print("Reading", filename)
    return pd.read_json(filename, orient="records").set_index("block_number")

def query_save(client, pool_address: str, event_type: str, sql: str):
    df = query(client, sql)
    save_queries(pool_address, event_type, df)

if not os.path.exists(args.pool_address):
    new_sql = 'select * from blockchain-etl.ethereum_balancer.BFactory_event_LOG_NEW_POOL where pool="{}"'.format(args.pool_address)
    swap_sql = 'select * from blockchain-etl.ethereum_balancer.BPool_event_LOG_SWAP where contract_address="{}" order by block_number'.format(args.pool_address)
    join_sql = 'select * from blockchain-etl.ethereum_balancer.BPool_event_LOG_JOIN where contract_address="{}" order by block_number'.format(args.pool_address)
    exit_sql = 'select * from blockchain-etl.ethereum_balancer.BPool_event_LOG_EXIT where contract_address="{}" order by block_number'.format(args.pool_address)
    transfer_sql = 'select * from blockchain-etl.ethereum_balancer.BPool_event_Transfer where contract_address="{}" order by block_number'.format(args.pool_address)
    with open("view_pools_fees.sql", "r") as f:
        fees_sql = f.read().format(args.pool_address)
    with open("view_pools_tokens_denorm_weights.sql", "r") as f:
        denorms_sql = f.read().format(args.pool_address)

    client = bigquery.Client()
    query_save(client, args.pool_address, "new", new_sql)
    query_save(client, args.pool_address, "join", join_sql)
    query_save(client, args.pool_address, "swap", swap_sql)
    query_save(client, args.pool_address, "exit", exit_sql)
    query_save(client, args.pool_address, "transfer", transfer_sql)
    query_save(client, args.pool_address, "fees", fees_sql)
    query_save(client, args.pool_address, "denorms", denorms_sql)

else:
    new_results = read_query_results(args.pool_address, "new")
    join_results = read_query_results(args.pool_address, "join")
    swap_results = read_query_results(args.pool_address, "swap")
    exit_results = read_query_results(args.pool_address, "exit")
    transfer_results = read_query_results(args.pool_address, "transfer")
    fees_results = read_query_results(args.pool_address, "fees")
    denorms_results = read_query_results(args.pool_address, "denorms")

    join_results["type"]="join"
    swap_results["type"]="swap"
    exit_results["type"]="exit"
    transfer_results["type"]="transfer"
    g = join_results.append(swap_results).append(exit_results).append(transfer_results)
    grouped_by_tx = g.groupby("transaction_hash")

    # Pandas, please don't truncate columns when I print them out
    pd.set_option('display.max_colwidth', None)

    # actions = []
    # print("df stuff")
    # for txhash, events in grouped_by_tx:
    #     if len(events) > 1:
    #         events["type"] = events["type"] + "_swap"

    #     e = events.to_dict(orient='index')
    #     # {272: {'block_number': 11558369,...}, 276: {'block_number':...}}

    #     subactions = [e[i] for i in e.keys()]
    #     # [{'block_number': 11558...}, {'block_number': ....}]
    #     actions.append(Action(tx_type=subactions[0]["type"], tx_hash=txhash, datetime=datetime.fromtimestamp(subactions[0]["block_timestamp"]/1000).isoformat(sep=" "), parameters=subactions))

    # actions_dict = [a.to_dict() for a in actions]

    # actions_filename = args.pool_address + "-actions.json"
    # print("saving to", actions_filename)
    # with open(actions_filename, 'w') as f:
    #     json.dump(actions_dict, f, indent="\t")
