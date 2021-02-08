import getopt
import json
import os
import sys

from attr import dataclass
from web3 import Web3, HTTPProvider
from json import load
from dataclasses_json import dataclass_json


class ERC20InfoReader:

    def __init__(self, w3):
        self.abi = [
            {
                "constant": True,
                "inputs": [],
                "name": "symbol",
                "outputs": [
                    {
                        "name": "",
                        "type": "string"
                    }
                ],
                "payable": False,
                "stateMutability": "view",
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "decimals",
                "outputs": [
                    {
                        "name": "",
                        "type": "uint8"
                    }
                ],
                "payable": False,
                "stateMutability": "view",
                "type": "function"
            },
        ]
        self.w3 = w3
        self.token_mapping = {}
        self.contract_mapping = {}

    def get_contract_for(self, address):
        if self.contract_mapping.get(address):
            return self.contract_mapping.get(address)
        contract = self.w3.eth.contract(address, abi=self.abi)
        self.contract_mapping[address] = contract
        return contract

    def get_token_symbol(self, address: str) -> str:
        address = Web3.toChecksumAddress(address)
        if self.token_mapping.get(address):
            if self.token_mapping[address].get('symbol'):
                return self.token_mapping.get(address).get('symbol')
        contract = self.get_contract_for(address)
        symbol = contract.functions.symbol().call()
        symbol = symbol.decode("utf-8")
        self.token_mapping[address] = {'symbol': symbol}
        return symbol

    def get_token_decimals(self, address: str) -> int:
        address = Web3.toChecksumAddress(address)
        if self.token_mapping.get(address):
            if self.token_mapping[address].get('decimals'):
                return self.token_mapping.get(address).get('decimals')
        contract = self.get_contract_for(address)
        decimals = contract.functions.decimals().call()
        print(decimals)
        self.token_mapping[address]['decimals'] = decimals
        return decimals

    def normalize_token_units(self, address: str, amount: any) -> str:
        decimals = self.get_token_decimals(address)
        if decimals == 18:
            return str(Web3.fromWei(int(amount), 'ether'))
        else:
            return str(amount // decimals)


class TransactionReceiptGetter:

    def __init__(self, w3, pool_address):
        self.w3 = w3
        self.file_name = "{}/{}.json".format(pool_address, 'receipts')
        self.receipts = {}
        if os.path.exists(self.file_name):
            file = open(self.file_name)
            self.receipts = json.load(file)
            file.close()

    def get_transaction_receipt(self, tx_hash: str):
        if self.receipts.get(tx_hash):
            return self.receipts['tx_hash']
        else:
            receipt = self.w3.eth.getTransactionReceipt(tx_hash)
            self.receipts[tx_hash] = receipt
            self.save()
            return receipt

    def save(self):
        json_object = json.dumps(self.receipts, indent=4)
        print('Writing', self.file_name)
        with open(self.file_name, "w") as outfile:
            outfile.write(json_object)


class BPoolLogCallParser:
    b_pool_method_signatures = {
        '0x8201aa3f': 'swapExactAmountIn',
        '0x7c5e9ea4': 'swapExactAmountOut',
        '0x6d06dfa0': 'joinswapPoolAmountOut',
        '0x5db34277': 'joinswapExternAmountIn',
        '0x4f69c0d4': 'joinPool',
        '0xb02f0b73': 'exitPool',
        '0x46ab38f1': 'exitswapPoolAmountIn',
        '0x02c96748': 'exitswapExternAmountOut',
        '0xe4e1e538': 'bind'
    }

    @dataclass_json
    @dataclass
    class ExitswapPoolAmountIn:
        token_out_address: str
        token_out_symbol: str
        pool_amount_in: str
        min_amount_out: str

    def __init__(self, erc20_info_reader: ERC20InfoReader):
        self.erc20_info_reader = erc20_info_reader
        file = open('./BPool.json', )
        abi_file = json.load(file)
        self.abi = abi_file['abi'].copy()
        file.close()

    def parse_from_receipt(self, receipt):
        anon_events = []
        for log in receipt.logs:
            for idx, topic in enumerate(log.topics):
                if idx == 0:
                    signature_candidate = Web3.toHex(topic[0:4])
                    method_name = BPoolLogCallParser.b_pool_method_signatures.get(signature_candidate)
                    if method_name is not None:
                        anon_events.append({
                            'type': method_name,
                            'inputs': self.parse_method(method_name, signature_candidate, log.data)
                        })
        return anon_events

    def parse_method(self, method_name: str, signature: str, data: str):
        sig = signature.replace("0x", "")
        encoded_arguments = data.split(sig)[1]
        args = {}
        method_abi = list(filter(lambda x: x.get('name') == method_name, self.abi))[0]
        step_number = 0
        initial = 0
        step = 64
        for i in range(0, len(encoded_arguments), step):
            if step_number >= len(method_abi['inputs']):
                continue
            argument_meta = method_abi['inputs'][step_number]
            name = argument_meta['name']
            print(name)
            raw_value = encoded_arguments[initial:initial + step]
            '''
            input = {
                'type': argument_meta['type']
            }
            '''
            parsed_value = None
            if argument_meta['type'] == 'address':
                # input['value'] = BPoolLogCallParser.parse_address(raw_value)
                parsed_value = BPoolLogCallParser.parse_address(raw_value)
                print(parsed_value)
                args[f'{name}_symbol'] = self.erc20_info_reader.get_token_symbol(parsed_value)
            elif argument_meta['type'] == 'uint256':
                # input['value'] = BPoolLogCallParser.parse_token_amount(raw_value)
                parsed_value = BPoolLogCallParser.parse_token_amount(raw_value)
            else:
                print('type parsing not implemented', argument_meta['type'])
            # args[argument_meta['name']] = input
            args[name] = parsed_value
            initial += step
            step_number += 1
        self.normalize_amounts(method_name, args)
        return args

    def normalize_amounts(self, method_name, args):
        if method_name == 'bind':
            token_address = args['token']
            args['balance'] = self.erc20_info_reader.normalize_token_units(token_address, args['balance'])
            args['denorm'] = str(Web3.fromWei(args['denorm'], 'ether'))
        else:
            # BPool has 18 decimals
            if args.get('poolAmountOut'):
                args['poolAmountOut'] = str(Web3.fromWei(args['poolAmountOut'], 'ether'))
            if args.get('poolAmountIn'):
                args['poolAmountIn'] = str(Web3.fromWei(args['poolAmountIn'], 'ether'))
            if args.get('minPoolAmountOut'):
                args['minPoolAmountOut'] = str(Web3.fromWei(args['minPoolAmountOut'], 'ether'))
            # Token specific amounts need each token's decimals
            if 'tokenIn' in args:
                if 'tokenAmountIn' in args:
                    args['tokenAmountIn'] = self.erc20_info_reader.normalize_token_units(args['tokenIn'], args['tokenAmountIn'])
                elif 'maxAmountIn' in args:
                    args['maxAmountIn'] = self.erc20_info_reader.normalize_token_units(args['tokenIn'], args['maxAmountIn'])
            if 'tokenOut' in args:
                if 'tokenAmountOut' in args:
                    args['tokenAmountOut'] = self.erc20_info_reader.normalize_token_units(args['tokenOut'], args['tokenAmountOut'])
                if 'minAmountOut' in args:
                    args['minAmountOut'] = self.erc20_info_reader.normalize_token_units(args['tokenOut'], args['minAmountOut'])
            # Other inputs have 18
            if args.get('maxPrice'):
                args['maxPrice'] = str(Web3.fromWei(args['maxPrice'], 'ether'))

    @staticmethod
    def strip_leading_0_add_0x(value: str):
        value = value[-40:]
        return f'0x{value}'

    @staticmethod
    def parse_address(raw_address):
        raw_address = BPoolLogCallParser.strip_leading_0_add_0x(raw_address)
        if not Web3.isAddress(raw_address):
            raise Exception('NOT ADDRESS', raw_address)
        return Web3.toChecksumAddress(raw_address)

    @staticmethod
    def parse_token_amount(raw_value):
        hex = raw_value.lstrip('0')
        if hex == '':
            hex = '0'
        return Web3.toInt(hexstr=hex)


def main(argv):
    tx_hash = None
    node_url = None
    log_call_parser = BPoolLogCallParser()
    try:
        opts, args = getopt.getopt(argv, "ht:n:", ["tx-hash=", "node-url="])
    except getopt.GetoptError:
        print('w3_utils.py -t -n')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print(
                'w3_utils.py -n <node-url> -t <tx-hash>')
            sys.exit()
        elif opt in ("-t", "--tx-hash"):
            tx_hash = arg
        elif opt in ("-n", "--node-url"):
            node_url = arg
    w3 = Web3(Web3.HTTPProvider(node_url))
    print('tx', tx_hash)
    receipt = w3.eth.getTransactionReceipt(tx_hash)
    input_data = log_call_parser.parse_from_receipt(receipt)
    print(input_data)
    method_args = input_data['inputs']
    method_arg = list(filter((lambda x: x['type'] == 'address'), method_args))[0]
    token_address = method_arg['value']
    print(token_address)
    symbol_getter = ERC20InfoReader(w3)
    print(f'Symbol for {token_address} is: {symbol_getter.get_token_symbol(token_address)}')


if __name__ == "__main__":
    main(sys.argv[1:])
