import argparse
import json
import os
import pickle
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json
from web3 import Web3, HTTPProvider
from data.w3_utils import ERC20SymbolGetter, BPoolLogCallParser
from marshmallow import fields
from datetime import datetime

import pandas as pd
from dataclasses_json import dataclass_json, config
from google.cloud import bigquery
from decimal import Decimal

from get_logs import ERC20SymbolGetter

parser = argparse.ArgumentParser(prog="pulldata", description="Ask Google Bigquery about a particular Balancer pool. Remember to set GOOGLE_APPLICATION_CREDENTIALS from https://cloud.google.com/docs/authentication/getting-started")
parser.add_argument("pool_address")
parser.add_argument("-p", "--pickles", help="Use pickles instead of JSON (faster)", dest="pickles", action="store_true", default=False)
args = parser.parse_args()
w3 = Web3(Web3.HTTPProvider(os.environ['NODE_URL']))


@dataclass_json
@dataclass
class Action:
    timestamp: datetime = field(
        metadata=config(
            encoder=datetime.isoformat,
            decoder=datetime.fromisoformat,
            mm_field=fields.DateTime(format="iso")
        )
    )
    tx_hash: str
    block_number: str
    swap_fee: str
    denorms: dict
    action_type: str
    action: dict


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

def pickle_queries(pool_address: str, event_type: str, df: pd.DataFrame):
    filename = "{}/{}.pickle".format(pool_address, event_type)
    print("Pickling to", filename)
    with open(filename, 'wb') as f:
        pickle.dump(df, f)

def load_pickles(pool_address: str, event_type: str):
    filename = "{}/{}.pickle".format(pool_address, event_type)
    print("Unpickling from", filename)
    with open(filename, 'rb') as f:
        return pickle.load(f)

def read_query_results(pool_address: str, event_type: str) -> pd.DataFrame:
    filename = "{}/{}.json".format(pool_address, event_type)
    print("Reading", filename)
    return pd.read_json(filename, orient="records").set_index("block_number")


def query_save(client, pool_address: str, event_type: str, sql: str):
    df = query(client, sql)
    save_queries(pool_address, event_type, df)

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

        writer = query_save if not args.pickles else pickle_queries
        writer(client, args.pool_address, "new", new_sql)
        writer(client, args.pool_address, "join", join_sql)
        writer(client, args.pool_address, "swap", swap_sql)
        writer(client, args.pool_address, "exit", exit_sql)
        writer(client, args.pool_address, "transfer", transfer_sql)
        writer(client, args.pool_address, "fees", fees_sql)
        writer(client, args.pool_address, "denorms", denorms_sql)

    else:
        reader = read_query_results if not args.pickles else load_pickles
        new_results = reader(args.pool_address, "new")
        join_results = reader(args.pool_address, "join")
        swap_results = reader(args.pool_address, "swap")
        exit_results = reader(args.pool_address, "exit")
        transfer_results = reader(args.pool_address, "transfer")
        fees_results = reader(args.pool_address, "fees")
        denorms_results = reader(args.pool_address, "denorms")

        new_results["type"]="new"
        join_results["type"]="join"
        swap_results["type"]="swap"
        exit_results["type"]="exit"
        transfer_results["type"]="transfer"

        # Later we will drop the column "address" from denorms, because it is
        # just the pool address - it never changes.
        denorms_results.drop(["address"], axis=1, inplace=True)
        # Using loc is slow. To avoid costly lookups by block_number, we convert
        # swapFee lookups into a dict, and denorms too
        fees_dict = fees_results.drop("address", axis=1).to_dict()["swapFee"]

        # Pandas, please don't truncate columns when I print them out
        pd.set_option('display.max_colwidth', None)

        def turn_events_into_actions(events_list):
            actions = []
            grouped = events_list.groupby("transaction_hash")
            for txhash, events in grouped:
                # Get basic info from first event log, no matter how many there actually are
                first_event_log = events.iloc[0]
                ts = first_event_log["block_timestamp"]
                tx_hash = first_event_log["transaction_hash"]
                block_number = first_event_log.name

                # Invariant data that exists parallel to these actions. Merge them
                # into the same Action object as a "context" for convenience.
                fee = fees_dict[block_number]
                denorms = denorms_results.loc[block_number].to_dict(orient="records")

                # convert block_number and swap_fee to string to painlessly
                # convert to JSON later (numpy.int64 can't be JSON serialized)
                a = Action(timestamp=datetime.fromtimestamp(ts/1000), tx_hash=tx_hash, block_number=str(block_number), swap_fee=str(fee), denorms=denorms, action_type=first_event_log["type"], action=events.to_dict(orient="records"))
                actions.append(a)

            return actions

        actions = []
        actions.extend(turn_events_into_actions(new_results))
        actions.extend(turn_events_into_actions(join_results))
        actions.extend(turn_events_into_actions(swap_results))
        actions.extend(turn_events_into_actions(exit_results))
        actions.extend(turn_events_into_actions(transfer_results))

        actions.sort(key=lambda a: a.timestamp)
        actions_dict = [a.to_dict() for a in actions]  # ridiculous that I have to do this, what am I importing dataclasses-json for

        actions_filename = args.pool_address + "-actions.json"
        print("saving to", actions_filename)
        with open(actions_filename, 'w') as f:
            json.dump(actions_dict, f, indent="\t")


import cProfile, pstats, io
from pstats import SortKey
pr = cProfile.Profile()
pr.enable()
produce_actions()
pr.disable()
s = io.StringIO()
sortby = SortKey.CUMULATIVE
ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
ps.print_stats(40)
print(s.getvalue())
