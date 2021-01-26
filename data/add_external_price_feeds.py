import getopt
import sys
import pandas as pd


def parse_price_feeds(price_feed_paths: [], token_symbols: []) -> []:
    if len(price_feed_paths) != len(token_symbols):
        raise Exception('Number of pricefeeds and tokens is different')
    result = {
        'datetime': [],
        'action': []
    }
    result_df = None
    prev_token = None
    for idx, path in enumerate(price_feed_paths):
        print(path)
        token = token_symbols[idx]
        print(token)
        parsed_price_feed = pd.read_csv(path, sep=';')
        parsed_price_feed = parsed_price_feed.set_index('time')
        print(parsed_price_feed)

        for i, row in parsed_price_feed.iterrows():
            


    return result



def main(argv):
    inputfile = ''
    outputfile = ''
    tokens = []
    price_feed_paths = []
    price_feeds = {}
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


if __name__ == "__main__":
    main(sys.argv[1:])
