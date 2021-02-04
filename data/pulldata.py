from decimal import Decimal

import pandas as pd
import argparse
import os
import json
from google.cloud import bigquery
from datetime import datetime
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json
from web3 import Web3, HTTPProvider

from data.w3_utils import ERC20SymbolGetter, BPoolLogCallParser

parser = argparse.ArgumentParser(prog="balancerpool",
                                 description="Ask Google Bigquery about a particular Balancer pool. Remember to set GOOGLE_APPLICATION_CREDENTIALS from https://cloud.google.com/docs/authentication/getting-started")
parser.add_argument("pool_address")
args = parser.parse_args()
w3 = Web3(Web3.HTTPProvider(os.environ['NODE_URL']))


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


def produce_actions():
    if not os.path.exists(args.pool_address):
        new_sql = 'select * from blockchain-etl.ethereum_balancer.BFactory_event_LOG_NEW_POOL where pool="{}"'.format(args.pool_address)
        swap_sql = 'select * from blockchain-etl.ethereum_balancer.BPool_event_LOG_SWAP where contract_address="{}" order by block_number'.format(
            args.pool_address)
        join_sql = 'select * from blockchain-etl.ethereum_balancer.BPool_event_LOG_JOIN where contract_address="{}" order by block_number'.format(
            args.pool_address)
        exit_sql = 'select * from blockchain-etl.ethereum_balancer.BPool_event_LOG_EXIT where contract_address="{}" order by block_number'.format(
            args.pool_address)
        transfer_sql = 'select * from blockchain-etl.ethereum_balancer.BPool_event_Transfer where contract_address="{}" order by block_number'.format(
            args.pool_address)
        with open("view_pools_fees.sql", "r") as f:
            fees_sql = f.read().format(args.pool_address)
        with open("view_pools_tokens_denorm_weights.sql", "r") as f:
            denorms_sql = f.read().format(args.pool_address)

        client = bigquery.Client()
        query_save(client, args.pool_address, "new", new_sql)
        query_save(client, args.pool_address, "fees", fees_sql)
        query_save(client, args.pool_address, "transfer", transfer_sql)
        '''query_save(client, args.pool_address, "join", join_sql)
        query_save(client, args.pool_address, "swap", swap_sql)
        query_save(client, args.pool_address, "exit", exit_sql)
        query_save(client, args.pool_address, "denorms", denorms_sql)'''

    else:
        new_results = read_query_results(args.pool_address, "new")
        fees_results = read_query_results(args.pool_address, "fees")
        transfer_results = read_query_results(args.pool_address, "transfer")
        '''join_results = read_query_results(args.pool_address, "join")
        swap_results = read_query_results(args.pool_address, "swap")
        exit_results = read_query_results(args.pool_address, "exit")
        denorms_results = read_query_results(args.pool_address, "denorms")

        join_results["type"] = "join"
        swap_results["type"] = "swap"
        exit_results["type"] = "exit"
        transfer_results["type"] = "transfer"
        g = join_results.append(swap_results).append(exit_results).append(transfer_results)
        grouped_by_tx = g.groupby("transaction_hash")'''

        # Pandas, please don't truncate columns when I print them out
        pd.set_option('display.max_colwidth', None)
        produce_initial_state(new_results, fees_results, transfer_results)
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



def get_initial_token_distribution(new_results) -> dict:
    receipt = w3.eth.getTransactionReceipt(new_results.iloc[0]['transaction_hash'])
    log_call_parser = BPoolLogCallParser()
    events = log_call_parser.parse_from_receipt(receipt)
    bind_events = list(filter(lambda x: x['type'] == 'bind', events))
    symbol_getter = ERC20SymbolGetter(w3)
    tokens = {}
    total_denorm_weight = 0
    for event in bind_events:
        inputs = event['inputs']
        token_address = list(filter(lambda x: x['name'] == 'token', inputs))[0]['value']
        token_symbol = symbol_getter.get_token_symbol(token_address)
        denorm = list(filter(lambda x: x['name'] == 'denorm', inputs))[0]['value']
        total_denorm_weight += denorm
        balance = list(filter(lambda x: x['name'] == 'balance', inputs))[0]['value']

        tokens[token_symbol] = {
            'weight': None,
            'denorm_weight': denorm,
            'balance': balance,
            'bound': True
        }
    for (key, token) in tokens.items():
        denorm = token['denorm_weight']
        token['weight'] = denorm / total_denorm_weight
    return tokens


def get_initial_pool_share(transfer_results, tx_hash):
    initial_tx_transfers = transfer_results.loc[transfer_results['transaction_hash'] == tx_hash]
    minting = initial_tx_transfers.loc[initial_tx_transfers['src'] == '0x0000000000000000000000000000000000000000']
    wei_amount = minting.iloc[0]['amt']
    return pd.np.true_divide(wei_amount, 10**18)


def produce_initial_state(new_results, fees_results, transfer_results):
    tokens = get_initial_token_distribution(new_results)
    swap_fee_weis = fees_results.iloc[0]['swapFee']
    swap_fee = pd.np.true_divide(swap_fee_weis, 10**18)
    pool_shares = get_initial_pool_share(transfer_results, new_results.iloc[0]['transaction_hash'])
    creation_date = datetime.fromtimestamp(new_results.iloc[0]['block_timestamp'] / 1000).utcnow().isoformat()
    initial_states = {
        'pool': {
            'tokens': tokens,
            'generated_fees': 0.0,
            'pool_shares': pool_shares,
            'swap_fee': swap_fee
        },
        'action_type': 'pool_creation',
        'change_datetime': creation_date

    }
    print(initial_states)


produce_actions()
