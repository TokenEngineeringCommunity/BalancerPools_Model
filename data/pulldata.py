import argparse
import json
import os
import pickle
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json
from web3 import Web3, HTTPProvider
from w3_utils import ERC20InfoReader, BPoolLogCallParser, TransactionReceiptGetter
from marshmallow import fields
from datetime import datetime
import time

import pandas as pd
from dataclasses_json import dataclass_json, config
from google.cloud import bigquery
from decimal import Decimal

parser = argparse.ArgumentParser(prog="pulldata",
                                 description="Ask Google Bigquery about a particular Balancer pool. Remember to set GOOGLE_APPLICATION_CREDENTIALS from https://cloud.google.com/docs/authentication/getting-started")
parser.add_argument("pool_address")
parser.add_argument("-p", "--pickles", help="Use pickles instead of JSON (faster)", dest="pickles", action="store_true", default=False)
args = parser.parse_args()
w3 = Web3(Web3.HTTPProvider(os.environ['NODE_URL']))
erc20_info_getter = ERC20InfoReader(w3)
log_call_parser = BPoolLogCallParser(erc20_info_getter)
receipt_getter = TransactionReceiptGetter(w3, args.pool_address)
ZERO_ADDRESS = '0x0000000000000000000000000000000000000000'


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


def save_queries_json(pool_address: str, event_type: str, df: pd.DataFrame):
    print("Saving to", pool_address)
    if not os.path.exists(args.pool_address):
        os.mkdir(pool_address)
    df.to_json("{}/{}.json".format(pool_address, event_type), orient="records")


def save_queries_pickle(pool_address: str, event_type: str, df: pd.DataFrame):
    filename = "{}/{}.pickle".format(pool_address, event_type)
    print("Pickling to", filename)
    if not os.path.exists(args.pool_address):
        os.mkdir(pool_address)
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


def query_and_save(client, pool_address: str, event_type: str, sql: str, writer):
    df = query(client, sql)
    writer(pool_address, event_type, df)


def get_initial_token_distribution(new_results) -> dict:
    receipt = w3.eth.getTransactionReceipt(new_results.iloc[0]['transaction_hash'])
    events = log_call_parser.parse_from_receipt(receipt)
    bind_events = list(filter(lambda x: x['type'] == 'bind', events))
    tokens = {}
    total_denorm_weight = Decimal('0.0')
    for event in bind_events:
        inputs = event['inputs']
        token_address = inputs['token']
        token_symbol = erc20_info_getter.get_token_symbol(token_address)
        denorm = Decimal(inputs['denorm'])
        total_denorm_weight += denorm

        tokens[token_symbol] = {
            'weight': None,
            'denorm_weight': str(denorm),
            'balance': inputs['balance'],
            'bound': True
        }
    for (key, token) in tokens.items():
        denorm = Decimal(token['denorm_weight'])
        token['weight'] = str(denorm / total_denorm_weight)
    return tokens


def get_initial_pool_share(transfer_results, tx_hash):
    initial_tx_transfers = transfer_results.loc[transfer_results['transaction_hash'] == tx_hash]
    minting = initial_tx_transfers.loc[initial_tx_transfers['src'] == '0x0000000000000000000000000000000000000000']
    wei_amount = int(minting.iloc[0]['amt'])
    return Web3.fromWei(wei_amount, 'ether')


def produce_initial_state(new_results, fees_results, transfer_results):
    tokens = get_initial_token_distribution(new_results)
    swap_fee_weis = int(fees_results.iloc[0]['swapFee'])
    swap_fee = Web3.fromWei(swap_fee_weis, 'ether')
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
    initial_states_filename = args.pool_address + "-initial_pool_states.json"
    print("saving to", initial_states_filename)
    with open(initial_states_filename, 'w') as f:
        json.dump(initial_states, f, indent="\t")


def format_denorms(denorms: dict):
    for item in denorms:
        item['token_address'] = Web3.toChecksumAddress(item['token_address'])
        item['token_symbol'] = erc20_info_getter.get_token_symbol(item['token_address'])
        item['denorm'] = str(Web3.fromWei(item['denorm'], 'ether'))


def classify_pool_share_transfers(transfers: []) -> (str, str):
    pool_share_burnt = list(filter(lambda x: x['dst'] == ZERO_ADDRESS, transfers))
    if len(pool_share_burnt) > 0:
        return 'pool_amount_in', str(Web3.fromWei(pool_share_burnt[0]['amt'], 'ether'))
    pool_share_minted = list(filter(lambda x: x['src'] == ZERO_ADDRESS, transfers))
    if len(pool_share_minted) > 0:
        return 'pool_amount_out', str(Web3.fromWei(pool_share_minted[0]['amt'], 'ether'))
    raise Exception('not pool share mint or burn', transfers)


def map_token_amounts(txs: [], address_key: str, amount_key: str, output_key: str):
    def map_tx(x):
        mapped = {}
        symbol = erc20_info_getter.get_token_symbol(x[address_key])
        mapped[symbol] = erc20_info_getter.normalize_token_units(x[address_key], x[amount_key])
        return mapped

    mapped_joins = list(map(map_tx, txs))
    return output_key, mapped_joins


def classify_actions(group):
    action = {}
    transfers = list(filter(lambda x: x['action_type'] == 'transfer', group))
    if len(transfers) > 0:
        key, value = classify_pool_share_transfers(transfers[0]['action'])
        action[key] = value
    joins = list(filter(lambda x: x['action_type'] == 'join', group))
    if len(joins) > 0:
        key, value = map_token_amounts(joins[0]['action'], address_key='tokenIn', amount_key='tokenAmountIn', output_key='tokens_in')
        action[key] = value
    exits = list(filter(lambda x: x['action_type'] == 'exit', group))
    if len(exits) > 0:
        key, value = map_token_amounts(exits[0]['action'], address_key='tokenOut', amount_key='tokenAmountOut', output_key='tokens_out')
        action[key] = value
    swaps = list(filter(lambda x: x['action_type'] == 'swap', group))
    if len(swaps) > 0:
        swap_result = {}
        in_key, in_value = map_token_amounts(swaps[0]['action'], address_key='tokenIn', amount_key='tokenAmountIn', output_key='tokens_in')
        swap_result[in_key] = in_value
        out_key, out_value = map_token_amounts(swaps[0]['action'], address_key='tokenOut', amount_key='tokenAmountOut',
                                               output_key='tokens_out')
        swap_result[out_key] = out_value
        action['swap'] = swap_result
    return action


def merge_actions(group):
    merged_action = {
        "timestamp": group[0]['timestamp'],
        "tx_hash": group[0]['tx_hash'],
        "block_number": group[0]['block_number'],
        "swap_fee": str(Web3.fromWei(int(group[0]['swap_fee']), 'ether')),
        "denorms": group[0]['denorms']
    }
    time.sleep(0.1)
    receipt = w3.eth.getTransactionReceipt(merged_action['tx_hash'])
    input_data = log_call_parser.parse_from_receipt(receipt)
    merged_action['contract_call'] = input_data
    merged_action['action'] = classify_actions(group)
    return merged_action


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

        writer = save_queries_json if not args.pickles else save_queries_pickle
        query_and_save(client, args.pool_address, "new", new_sql, writer)
        query_and_save(client, args.pool_address, "join", join_sql, writer)
        query_and_save(client, args.pool_address, "swap", swap_sql, writer)
        query_and_save(client, args.pool_address, "exit", exit_sql, writer)
        query_and_save(client, args.pool_address, "transfer", transfer_sql, writer)
        query_and_save(client, args.pool_address, "fees", fees_sql, writer)
        query_and_save(client, args.pool_address, "denorms", denorms_sql, writer)

    else:
        reader = read_query_results if not args.pickles else load_pickles
        new_results = reader(args.pool_address, "new")
        join_results = reader(args.pool_address, "join")
        swap_results = reader(args.pool_address, "swap")
        exit_results = reader(args.pool_address, "exit")
        transfer_results = reader(args.pool_address, "transfer")
        fees_results = reader(args.pool_address, "fees")
        denorms_results = reader(args.pool_address, "denorms")

        new_results["type"] = "new"
        join_results["type"] = "join"
        swap_results["type"] = "swap"
        exit_results["type"] = "exit"
        transfer_results["type"] = "transfer"

        # Later we will drop the column "address" from denorms, because it is
        # just the pool address - it never changes.
        denorms_results.drop(["address"], axis=1, inplace=True)
        # Using loc is slow. To avoid costly lookups by block_number, we convert
        # swapFee lookups into a dict, and denorms too
        fees_dict = fees_results.drop("address", axis=1).to_dict()["swapFee"]

        # Pandas, please don't truncate columns when I print them out
        pd.set_option('display.max_colwidth', None)

        produce_initial_state(new_results, fees_results, transfer_results)

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
                format_denorms(denorms)
                # convert block_number and swap_fee to string to painlessly
                # convert to JSON later (numpy.int64 can't be JSON serialized)
                a = Action(timestamp=datetime.fromtimestamp(ts / 1000), tx_hash=tx_hash, block_number=str(block_number), swap_fee=str(fee),
                           denorms=denorms, action_type=first_event_log["type"], action=events.to_dict(orient="records"))
                actions.append(a)

            return actions

        actions = []
        actions.extend(turn_events_into_actions(new_results))
        actions.extend(turn_events_into_actions(join_results))
        actions.extend(turn_events_into_actions(swap_results))
        actions.extend(turn_events_into_actions(exit_results))
        actions.extend(turn_events_into_actions(transfer_results))

        grouped_by_tx_actions = {}
        for i, action in enumerate(actions):
            tx_hash = actions[i].tx_hash
            if grouped_by_tx_actions.get(tx_hash) is None:
                grouped_by_tx_actions[tx_hash] = []
            grouped_by_tx_actions[tx_hash].append(action.to_dict())
        grouped_actions = list(map(lambda key: grouped_by_tx_actions[key], grouped_by_tx_actions))

        # Filter out pool share transfer
        grouped_actions = list(filter(lambda acts: not (len(acts) == 1 and acts[0]['action_type'] == 'transfer'), grouped_actions))

        # Combine events
        grouped_actions = list(map(merge_actions, grouped_actions))

        grouped_actions.sort(key=lambda a: a['timestamp'])
        # actions_dict = [a.to_dict() for a in actions]  # ridiculous that I have to do this, what am I importing dataclasses-json for

        actions_filename = args.pool_address + "-actions.json"
        print("saving to", actions_filename)
        with open(actions_filename, 'w') as f:
            json.dump(grouped_actions, f, indent="\t")


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
