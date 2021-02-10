import getopt
import json
import os
import sys
import pickle

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
        self.token_mapping = {'0x9f8F72aA9304c8B593d555F12eF6589cC3A579A2': {'symbol': 'MKR', 'decimals': 18}, '0xba100000625a3754423978a60c9317c58a424e3D': {'symbol': 'BAL', 'decimals': 18}, '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2': {'symbol': 'WETH', 'decimals': 18}, '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48': {'symbol': 'USDC', 'decimals': 6}, '0x6B175474E89094C44Da98b954EedeAC495271d0F': {'symbol': 'DAI', 'decimals': 18}, '0x985dd3D42De1e256d09e1c10F112bCCB8015AD41': {'symbol': 'OCEAN', 'decimals': 18}, '0x5d3a536E4D6DbD6114cc1Ead35777bAB948E3643': {'symbol': 'cDAI', 'decimals': 8}, '0xc00e94Cb662C3520282E6f5717214004A7f26888': {'symbol': 'COMP', 'decimals': 18}, '0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599': {'symbol': 'WBTC', 'decimals': 8}, '0x45f24BaEef268BB6d63AEe5129015d69702BCDfa': {'symbol': 'YFV', 'decimals': 18}, '0x514910771AF9Ca656af840dff83E8264EcF986CA': {'symbol': 'LINK', 'decimals': 18}, '0xad32A8e6220741182940c5aBF610bDE99E737b2D': {'symbol': 'DOUGH', 'decimals': 18}, '0xbC396689893D065F41bc2C6EcbeE5e0085233447': {'symbol': 'PERP', 'decimals': 18}, '0x1cEB5cB57C4D4E2b2433641b95Dd330A33185A44': {'symbol': 'KP3R', 'decimals': 18}, '0x04Fa0d235C4abf4BcF4787aF4CF447DE572eF828': {'symbol': 'UMA', 'decimals': 18}, '0x80fB784B7eD66730e8b1DBd9820aFD29931aab03': {'symbol': 'LEND', 'decimals': 18}, '0x56d811088235F11C8920698a204A5010a788f4b3': {'symbol': 'BZRX', 'decimals': 18}, '0x9Cb2f26A23b8d89973F08c957C4d7cdf75CD341c': {'symbol': 'DZAR', 'decimals': 6}, '0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984': {'symbol': 'UNI', 'decimals': 18}, '0xD533a949740bb3306d119CC777fa900bA034cd52': {'symbol': 'CRV', 'decimals': 18}, '0xEd91879919B71bB6905f23af0A68d231EcF87b14': {'symbol': 'DMG', 'decimals': 18}, '0x0bc529c00C6401aEF6D220BE8C6Ea1667F6Ad93e': {'symbol': 'YFI', 'decimals': 18}, '0x0e511Aa1a137AaD267dfe3a6bFCa0b856C1a3682': {'symbol': 'BPT', 'decimals': 18}, '0xC011a73ee8576Fb46F5E1c5751cA3B9Fe0af2a6F': {'symbol': 'SNX', 'decimals': 18}, '0xa117000000f279D81A1D3cc75430fAA017FA5A2e': {'symbol': 'ANT', 'decimals': 18}, '0x40FD72257597aA14C7231A7B1aaa29Fce868F677': {'symbol': 'XOR', 'decimals': 18}, '0xdd974D5C2e2928deA5F71b9825b8b646686BD200': {'symbol': 'KNC', 'decimals': 18}, '0x0E29e5AbbB5FD88e28b2d355774e73BD47dE3bcd': {'symbol': 'HAKKA', 'decimals': 18}, '0x408e41876cCCDC0F92210600ef50372656052a38': {'symbol': 'REN', 'decimals': 18}, '0x056Fd409E1d7A124BD7017459dFEa2F387b6d5Cd': {'symbol': 'GUSD', 'decimals': 2}, '0x5dbcF33D8c2E976c6b560249878e6F1491Bca25c': {'symbol': 'yyDAI+yUSDC+yUSDT+yTUSD', 'decimals': 18}, '0xB81D70802a816B5DacBA06D708B5acF19DcD436D': {'symbol': 'DEXG', 'decimals': 18}, '0xEB4C2781e4ebA804CE9a9803C67d0893436bB27D': {'symbol': 'renBTC', 'decimals': 8}, '0x0d438F3b5175Bebc262bF23753C1E53d03432bDE': {'symbol': 'wNXM', 'decimals': 18}, '0x8A9C67fee641579dEbA04928c4BC45F66e26343A': {'symbol': 'JRT', 'decimals': 18}, '0xAba8cAc6866B83Ae4eec97DD07ED254282f6aD8A': {'symbol': 'YAMv2', 'decimals': 24}, '0xe2f2a5C287993345a840Db3B0845fbC70f5935a5': {'symbol': 'mUSD', 'decimals': 18}, '0xeca82185adCE47f39c684352B0439f030f860318': {'symbol': 'PERL', 'decimals': 18}, '0x0Ae055097C6d159879521C384F1D2123D1f195e6': {'symbol': 'STAKE', 'decimals': 18}, '0xBBbbCA6A901c926F240b89EacB641d8Aec7AEafD': {'symbol': 'LRC', 'decimals': 18}, '0x8f8221aFbB33998d8584A2B05749bA73c37a938a': {'symbol': 'REQ', 'decimals': 18}}
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
        if address == '0x9f8f72aa9304c8b593d555f12ef6589cc3a579a2':
            # For some reason, MKR implementation makes Web3py crash
            self.token_mapping[address] = {'symbol': 'MKR'}
            return 'MKR'
        contract = self.get_contract_for(address)
        bsymbol = contract.functions.symbol().call()
        symbol = Web3.toText(bsymbol)
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
            return str(int(amount) // decimals)


class TransactionReceiptGetter:

    def __init__(self, w3, pool_address):
        self.w3 = w3
        self.file_name = "{}/{}.pickle".format(pool_address, 'receipts')
        self.receipts = {}
        if os.path.exists(self.file_name):
            file = open(self.file_name)
            self.receipts = pickle.load(file)
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
        print('Writing', self.file_name)
        with open(self.file_name, "wb") as outfile:
            pickle.dump(self.receipts, outfile)


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
        file = open('./v1-abi.json', )
        abi_file = json.load(file)
        self.abi = abi_file['abi'].copy()
        file.close()

    def parse_from_receipt(self, receipt, pool_address):
        anon_events = []
        for log in receipt.logs:
            if log.address.lower() != pool_address.lower():
                continue
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

'''
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
'''
