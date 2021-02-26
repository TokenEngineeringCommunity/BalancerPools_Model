import glob
import typing
import re
import pandas as pd
from datetime import datetime
import dateutil
import glob

from numpy.lib import math


def stage4_add_prices_to_initialstate_and_actions(pool_address: str, fiat_symbol: str, initial_state: typing.Dict, actions: typing.List[typing.Dict]):
    def parse_price_feeds(token_symbols: []) -> []:
        if len(price_feed_paths) != len(token_symbols):
            raise Exception('Number of pricefeeds and tokens is different')
        result_df = None
        for idx, path in enumerate(price_feed_paths):
            token = token_symbols[idx]
            print('Reading', path)
            parsed_price_feed = pd.read_csv(path, sep=';')
            parsed_price_feed[f'{token}'] = parsed_price_feed.apply(lambda row: (row.open + row.close) / 2, axis=1)
            if result_df is None:
                result_df = parsed_price_feed.filter(['time', f'{token}'], axis=1)
                result_df.rename(columns={'time': 'timestamp'}, inplace=True)
                result_df['timestamp'] = pd.to_datetime(result_df['timestamp'])
            else:
                result_df[f'{token}'] = parsed_price_feed[f'{token}']

        def generate_action(row):
            result = {'type': 'external_price_update', 'tokens': {}}
            for index, value in row.items():
                if index in token_symbols:
                    result['tokens'][index] = value
            return result

        result_df['action'] = result_df.apply(generate_action, axis=1)
        actions = result_df['action'].to_list()
        datetimes = result_df['timestamp'].to_list()
        result = []
        for idx, action in enumerate(actions):
            skip = False
            for token in action['tokens']:
                skip = math.isnan(action['tokens'][token])
            if skip:
                continue
            result.append({
                'timestamp': datetimes[idx],
                'fiat_currency': fiat_symbol,
                'action': action
            })

        return result

    def get_price_feeds_tokens(initial_state: typing.Dict):
        tokens = initial_state['pool']['tokens']
        token_symbols = []
        feeds_file_paths = []
        price_feeds = glob.glob(f'./{pool_address}/*.csv')
        for feed_name in price_feeds:
            for token in tokens:
                p = re.compile(token)
                result = p.search(feed_name)
                if result:
                    token_symbols.append(token)
                    feeds_file_paths.append(feed_name)
        return feeds_file_paths, token_symbols

    def add_price_feeds_to_actions(actions: typing.List[typing.Dict]) -> typing.List[typing.Dict]:
        actions.extend(price_actions)
        def equalize_date_types(action):
            if not isinstance(action['timestamp'], datetime):
                action['timestamp'] = dateutil.parser.isoparse(action['timestamp'])
            return action
        actions = list(map(equalize_date_types, actions))
        actions.sort(key=lambda x: x['timestamp'])

        def convert_to_iso_str(action):
            action['timestamp'] = action['timestamp'].isoformat()
            return action
        actions = list(map(convert_to_iso_str, actions))

        # Remove prices before pool creation. First action must be pool creation
        while actions[0]['action']['type'] != 'pool_creation':
            actions.pop(0)

        return actions

    def add_price_feeds_to_initial_state(price_actions, initial_state) -> typing.Dict:
        initial_prices = price_actions[0]
        initial_state['token_prices'] = initial_prices['action']['tokens']
        return initial_state

    price_feed_paths, tokens = get_price_feeds_tokens(initial_state)

    import ipdb; ipdb.set_trace()
    price_actions = parse_price_feeds(token_symbols=tokens)
    initial_state_w_prices = add_price_feeds_to_initial_state(price_actions, initial_state)
    actions_w_prices = add_price_feeds_to_actions(actions)

    return initial_state_w_prices, actions_w_prices
