import getopt
import json
import sys
import pandas as pd

def convert_to_action_json(actions, output_file_path):
    result = []
    action_index = None
    for idx, row in actions.iterrows():
        if action_index is None and row['action']['type'] == 'external_price_update':
            continue
        else:
            action_index = 0
        dict_row = row.to_dict()
        dict_row['index'] = action_index
        dict_row['datetime'] = idx.isoformat()
        dict_row['action']['datetime'] = idx.isoformat()
        action_index += 1
        result.append(dict_row)
    json_object = json.dumps(result, indent=4)
    # Writing to sample.json
    with open(output_file_path, "w") as outfile:
        outfile.write(json_object)

def add_price_feeds_to_actions(price_feeds, action_file_path):
    action_df = pd.read_json(action_file_path)
    action_df['datetime'] = pd.to_datetime(action_df['datetime'], utc=True)
    action_df = action_df.set_index('datetime')
    price_feeds = price_feeds.set_index('datetime')
    merged_df = action_df.append(price_feeds)
    return merged_df.sort_index()

def parse_price_feeds(price_feed_paths: [], token_symbols: []) -> []:
    if len(price_feed_paths) != len(token_symbols):
        raise Exception('Number of pricefeeds and tokens is different')
    result_df = None
    for idx, path in enumerate(price_feed_paths):
        token = token_symbols[idx]
        parsed_price_feed = pd.read_csv(path, sep=';')
        parsed_price_feed[f'{token}'] = parsed_price_feed.apply(lambda row: (row.open + row.close) / 2, axis=1)

        if result_df is None:
            result_df = parsed_price_feed.filter(['time', f'{token}'], axis=1)
            result_df.rename(columns={'time': 'datetime'}, inplace=True)
            result_df['datetime'] = pd.to_datetime(result_df['datetime'])
        else:
            result_df[f'{token}'] = parsed_price_feed[f'{token}']

    def generate_action(row):
        result = {'type': 'external_price_update', 'tokens': {}}
        for index, value in row.items():
            if index in token_symbols:
                result['tokens'][index] = value
        return result

    result_df['action'] = result_df.apply(generate_action, axis=1)

    return result_df


def main(argv):
    inputfile = ''
    outputfile = ''
    tokens = []
    price_feed_paths = []
    try:
        opts, args = getopt.getopt(argv, "hi:o:f:t:", ["ifile=", "ofile=", "price_feeds=", "tokens="])
    except getopt.GetoptError:
        print('add_external_price_feeds.py -i <input_action_file> -o <outputfile> -f <price_feeds separated by ,> -t <token_symbols separated by ,>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print(
                'add_external_price_feeds.py -i <input_action_file> -o <outputfile> -f <price_feeds separated by ,> -t <token_symbols separated by ,>')
            sys.exit()
        elif opt in ("-f", "--price_feeds"):
            price_feed_paths = arg.split(',')
        elif opt in ("-t", "--tokens"):
            tokens = arg.split(',')
        elif opt in ("-i", "--ifile"):
            inputfile = arg
        elif opt in ("-o", "--ofile"):
            outputfile = arg

    price_feeds = parse_price_feeds(price_feed_paths=price_feed_paths, token_symbols=tokens)
    merged_actions = add_price_feeds_to_actions(price_feeds, inputfile)
    convert_to_action_json(merged_actions, outputfile)

if __name__ == "__main__":
    main(sys.argv[1:])
