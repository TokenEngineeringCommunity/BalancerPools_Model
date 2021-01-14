import csv
import getopt
import json
import sys
import pprint
from collections import defaultdict

ZERO_ADDRESS = '0x0000000000000000000000000000000000000000'

def parse_token_tx(tx_dict: dict, row: dict):
    tx = tx_dict[row['Txhash']]
    if tx.get(row['TokenSymbol']) is None:
        tx[row['TokenSymbol']] = []
    tx[row['TokenSymbol']].append({
        'from': row['From'],
        'to': row['To'],
        'value': row['Value'].replace(',', '')
    })
    return tx_dict


def classify_txs(txs: dict, pool_address: str) -> dict:
    for tx_hash in txs:
        tx_info = txs[tx_hash]
        if tx_hash == '0x43fdd919d240ca7c69267219a53c0b7fdf805c27fc43f1c3133f0c369fcb1200':
            print('heyehey')
            pp = pprint.PrettyPrinter(indent=4)
            pp.pprint(tx_info)
        data_keys = tx_info.keys()
        if 'BPT' in data_keys:
            # exit or join
            pool_token_operations = tx_info['BPT']
            for bpt_tx in pool_token_operations:
                if bpt_tx['from'] == pool_address and bpt_tx['to'] != ZERO_ADDRESS:
                    tx_info['action_type'] = 'join'
                    print('join')
                    break
                elif bpt_tx['from'] == pool_address and bpt_tx['to'] == ZERO_ADDRESS:
                    tx_info['action_type'] = 'exit'
                    print('exit')
                    break
        else:
            tx_info['action_type'] = 'swap'
        if tx_info.get('action_type') is None:
            raise Exception('malformed tx')
    return txs


def get_grouped_txs(path: str) -> dict:
    with open(path, encoding='utf-8') as csvf:
        token_tx_list = csv.DictReader(csvf)
        result = defaultdict(lambda: False)
        for row in token_tx_list:
            if not result[row['Txhash']]:
                result[row['Txhash']] = {
                    'unixtimestamp': row['UnixTimestamp'],
                    'datetime': row['DateTime']
                }
            parse_token_tx(result, row)
        return result

def create_token_tx_file(input_file: str, output_file: str, pool_address: str):
    token_txs = classify_txs(txs=get_grouped_txs(input_file), pool_address=pool_address)
    # Serializing json
    json_object = json.dumps(token_txs, indent=4)

    # Writing to sample.json
    with open(output_file, "w") as outfile:
        outfile.write(json_object)


def main(argv):
    inputfile = ''
    outputfile = ''
    pool_address = None
    try:
        opts, args = getopt.getopt(argv, "hi:o:p:", ["ifile=", "ofile=", "paddress="])
    except getopt.GetoptError:
        print('convert_ethersca_csv.py -i <inputfile> -o <outputfile>  -p <pool_address>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('convert_ethersca_csv.py -i <inputfile> -o <outputfile> (optional) -p <pool_address>')
            sys.exit()
        elif opt in ("-p", "--paddress"):
            pool_address = arg.lower()
        elif opt in ("-i", "--ifile"):
            inputfile = arg
        elif opt in ("-o", "--ofile"):
            outputfile = arg
    if pool_address is None:
        raise Exception('pool address not provided')
    create_token_tx_file(input_file=inputfile, output_file=outputfile, pool_address=pool_address)


if __name__ == "__main__":
    main(sys.argv[1:])
