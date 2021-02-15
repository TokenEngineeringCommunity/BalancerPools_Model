import getopt
import json
import os
import sys
import re

import dateutil
import pandas as pd


def add_prices_to_actions(pool_address, fiat_symbol):

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
            result.append({
                'timestamp': datetimes[idx],
                'fiat_currency': fiat_symbol,
                'action': action
            })
        return result

    def get_price_feeds_tokens():
        with open(f'{pool_address}-initial_pool_states.json', "r") as read_file:
            initial_states = json.load(read_file)
            tokens = initial_states['pool']['tokens']
            token_symbols = []
            feeds_file_paths = []
            price_feeds = os.listdir(f'./{pool_address}-prices')
            for feed_name in price_feeds:
                for token in tokens:
                    p = re.compile(token)
                    result = p.search(feed_name)
                    if result:
                        token_symbols.append(token)
                        feeds_file_paths.append(f'./{pool_address}-prices/{feed_name}')
            return feeds_file_paths, token_symbols

    def add_price_feeds_to_actions_and_save():
        with open(f'{pool_address}-actions.json', "r") as read_file:
            actions = json.load(read_file)

            actions.extend(price_actions)
            def equalize_date_types(action):
                if isinstance(action['timestamp'], str):
                    action['timestamp'] = dateutil.parser.isoparse(action['timestamp'])
                else:
                    action['timestamp'] = action['timestamp'].to_pydatetime()
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

            actions_filename = pool_address + "-actions-prices.json"
            print("saving to", actions_filename)
            with open(actions_filename, 'w') as f:
                json.dump(actions, f, indent="\t")

    def add_price_feeds_to_initial_state_and_save():
        with open(f'{pool_address}-initial_pool_states.json', "r") as read_file:
            initial_prices = price_actions[0]
            initial_state = json.load(read_file)
            print(initial_prices)
            initial_state['token_prices'] = initial_prices['action']['tokens']
            initial_states_filenames = f'{pool_address}-initial_pool_states-prices.json'
            print("saving to", initial_states_filenames)
            with open(initial_states_filenames, 'w') as f:
                json.dump(initial_state, f, indent="\t")

    price_feed_paths, tokens = get_price_feeds_tokens()
    print(price_feed_paths)
    print(tokens)

    price_actions = parse_price_feeds(token_symbols=tokens)
    add_price_feeds_to_initial_state_and_save()
    add_price_feeds_to_actions_and_save()


def main(argv):
    pool_address = None
    fiat_symbol = ''
    tokens = []
    price_feed_paths = []
    try:
        opts, args = getopt.getopt(argv, "hp:f:", ["pool_address=", "fiat_symbol="])
    except getopt.GetoptError:
        print('add_external_price_feeds.py -p <pool_address> -f <fiat_symbol>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print(
                'add_external_price_feeds.py -p <pool_address> -f <fiat_symbol>')
            sys.exit()
        elif opt in ("-p", "--pool_address"):
            pool_address = arg
        elif opt in ("-f", "--fiat_symbol"):
            fiat_symbol = arg

    add_prices_to_actions(pool_address, fiat_symbol)


if __name__ == "__main__":
    main(sys.argv[1:])
