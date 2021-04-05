import argparse
from coingecko import add_prices_from_coingecko
from tradingview import stage4_add_prices_to_initialstate_and_actions
from utils import save_json, json_serialize_datetime


parser = argparse.ArgumentParser(prog="pullonlypricedata",
                                 description="Generate only price action file")
parser.add_argument("token_symbols", help="Comma separated tokens")
parser.add_argument("initial_timestamp", help="ISO 8601")
parser.add_argument("price_provider",
                    help="Can be either tradingview or coingecko. Tradingview requires the CSVs to already be in the pool_address subdirectory.")
parser.add_argument("--fiat", "-f", default="USD")
args = parser.parse_args()


def produce_actions():
    actions = [{
        "timestamp": args.initial_timestamp, #"2020-07-28T01:25:23+00:00",
        "action": {
            "type": "pool_creation"
        }
    }]
    initial_state = {
        'pool': {
            'tokens': {}
        },
        "change_datetime": args.initial_timestamp
    }
    tokens = args.token_symbols.split(",")
    for token in tokens:
        initial_state['pool']['tokens'][token] = {}

    if args.price_provider == "tradingview":
        initial_state_w_prices, actions_w_prices = stage4_add_prices_to_initialstate_and_actions(args.pool_address, args.fiat, initial_state, actions)
        save_json(initial_state_w_prices, f'{args.pool_address}-initial_pool_states-prices.json')
        save_json(actions_w_prices, f'{args.pool_address}-actions-only-prices.json')
    elif args.price_provider == "coingecko":
        initial_state_w_prices, actions = add_prices_from_coingecko(initial_state, actions, args.pool_address, args.fiat)
        save_json(initial_state_w_prices, f'{args.pool_address}-initial_pool_states-prices.json', default=json_serialize_datetime)
        save_json(actions, f'{args.pool_address}-actions-only-prices.json', default=json_serialize_datetime)
    else:
        raise Exception("Wait a minute, {} is not a valid price provider".format(args.price_provider))


from ipdb import launch_ipdb_on_exception

with launch_ipdb_on_exception():
    produce_actions()
