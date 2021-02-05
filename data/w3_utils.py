import getopt
import json
import sys

from web3 import Web3, HTTPProvider
from json import load


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

    def __init__(self):
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
        args = []
        method_abi = list(filter(lambda x: x.get('name') == method_name, self.abi))[0]
        step_number = 0
        initial = 0
        step = 64
        for i in range(0, len(encoded_arguments), step):
            if step_number >= len(method_abi['inputs']):
                continue
            argument_meta = method_abi['inputs'][step_number]
            raw_value = encoded_arguments[initial:initial + step]
            input = {
                'name': argument_meta['name'],
                'type': argument_meta['type']
            }
            if argument_meta['type'] == 'address':
                input['value'] = BPoolLogCallParser.parse_address(raw_value)
            elif argument_meta['type'] == 'uint256':
                input['value'] = BPoolLogCallParser.parse_token_amount(raw_value)
            else:
                print('type parsing not implemented', argument_meta['type'])
            args.append(input)
            initial += step
            step_number += 1
        return args

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
        weis = Web3.toInt(hexstr=hex)
        return Web3.fromWei(weis, 'ether')


class ERC20SymbolGetter:
    def __init__(self, w3):
        self.abi = [{
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
        }]
        self.w3 = w3
        self.token_mapping = {}

    def get_token_symbol(self, address: str) -> str:
        if self.token_mapping.get(address):
            return self.token_mapping.get(address)
        contract = self.w3.eth.contract(address, abi=self.abi)
        symbol = contract.functions.symbol().call()
        self.token_mapping[address] = symbol
        return symbol


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
    symbol_getter = ERC20SymbolGetter(w3)
    print(f'Symbol for {token_address} is: {symbol_getter.get_token_symbol(token_address)}')


if __name__ == "__main__":
    main(sys.argv[1:])
