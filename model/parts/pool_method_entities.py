from decimal import Decimal

from attr import dataclass


@dataclass
class TokenAmount:
    symbol: str
    amount: Decimal

    @staticmethod
    def ta_with_dict(token_dict):
        return TokenAmount(token_dict['symbol'], Decimal(token_dict['amount']))


@dataclass
class JoinParamsInput:
    pool_amount_out: Decimal
    tokens_in: [str]


@dataclass
class JoinParamsOutput:
    tokens_in: [TokenAmount]

@dataclass
class JoinSwapExternAmountInInput(object):
    token_in: TokenAmount

@dataclass
class JoinSwapExternAmountInOutput(object):
    pool_amount_out: Decimal

@dataclass
class JoinSwapPoolAmountOutInput(object):
    pass

@dataclass
class JoinSwapPoolAmountOutOutput(object):
    pass

@dataclass
class SwapExactAmountInInput(object):
    token_in: TokenAmount
    min_token_out: TokenAmount

@dataclass
class SwapExactAmountInOutput(object):
    token_out: TokenAmount

@dataclass
class SwapExactAmountOutInput(object):
    max_token_in: TokenAmount
    token_out: TokenAmount

@dataclass
class SwapExactAmountOutOutput(object):
    token_in: TokenAmount

@dataclass
class ExitPoolInput(object):
    pool_amount_in: Decimal

@dataclass
class ExitPoolOutput(object):
    tokens_out: [TokenAmount]

@dataclass
class ExitSwapPoolAmountInInput(object):
    pool_amount_in: Decimal

@dataclass
class ExitSwapPoolAmountInOutput(object):
    token_out: TokenAmount

@dataclass
class ExitSwapPoolExternAmountOutInput(object):
    token_out: TokenAmount
    max_pool_in: Decimal

@dataclass
class ExitSwapPoolExternAmountOutOutput(object):
    pool_amount_in: Decimal


class PoolMethodParamsDecoder:

    @staticmethod
    def join_pool_simplified(action: dict) -> (JoinParamsInput, JoinParamsOutput):
        tokens_in = action['tokens_in']
        join_input = JoinParamsInput(action['pool_amount_out'], list(filter(lambda x: x['symbol'], tokens_in)))
        join_output = JoinParamsOutput(list(map(lambda x: TokenAmount.ta_with_dict(x), tokens_in)))
        return join_input, join_output

    @staticmethod
    def join_pool_contract_call(action: dict, contract_call: dict) -> (JoinParamsInput, JoinParamsOutput):
        tokens_in = action['tokens_in']
        join_input = JoinParamsInput(contract_call['poolAmountOut'], list(filter(lambda x: x['symbol'], tokens_in)))
        join_output = JoinParamsOutput(list(map(lambda x: TokenAmount.ta_with_dict(x), tokens_in)))
        return join_input, join_output

    @staticmethod
    def join_swap_extern_amount_in_simplified(action: dict) -> (JoinSwapExternAmountInInput, JoinSwapExternAmountInOutput):
        join_swap_input = JoinSwapExternAmountInInput(TokenAmount.ta_with_dict(action['token_in']))
        join_swap_output = JoinSwapExternAmountInOutput(Decimal(action['pool_amount_out']))
        return join_swap_input, join_swap_output

    @staticmethod
    def join_swap_extern_amount_in_contract_call(action: dict, contract_call: dict) -> (JoinSwapExternAmountInInput, JoinSwapExternAmountInOutput):
        join_swap_input = JoinSwapExternAmountInInput(TokenAmount(contract_call['inputs']['tokenIn_symbol'], contract_call['inputs']['tokenAmountIn']))
        join_swap_output = JoinSwapExternAmountInOutput(Decimal(action['pool_amount_out']))
        return join_swap_input, join_swap_output

    @staticmethod
    def join_swap_pool_amount_out_contract_call(action: dict, contract_call: dict) -> (JoinSwapPoolAmountOutInput, JoinSwapPoolAmountOutOutput):
        # TODO
        pass

    @staticmethod
    def swap_exact_amount_in_simplified(action: dict) -> (SwapExactAmountInInput, SwapExactAmountInOutput):
        swap_input = SwapExactAmountInInput(token_in=TokenAmount.ta_with_dict(action['token_in']), min_token_out=TokenAmount.ta_with_dict(action['token_out']))
        swap_output = SwapExactAmountInOutput(TokenAmount.ta_with_dict(action['token_out']))
        return swap_input, swap_output

    @staticmethod
    def swap_exact_amount_in_contract_call(action: dict, contract_call: dict) -> (SwapExactAmountInInput, SwapExactAmountInOutput):
        token_in = TokenAmount(symbol=contract_call['inputs']['tokenIn_symbol'], amount=contract_call['inputs']['tokenAmountIn'])
        min_token_out = TokenAmount(symbol=contract_call['inputs']['tokenOut_symbol'], amount=contract_call['inputs']['minAmountOut'])
        swap_input = SwapExactAmountInInput(token_in=token_in,
                                            min_token_out=min_token_out)
        swap_output = SwapExactAmountInOutput(TokenAmount.ta_with_dict(action['token_out']))
        return swap_input, swap_output
    
    @staticmethod
    def swap_exact_amount_out_contract_call(action: dict, contract_call: dict) -> (SwapExactAmountOutInput, SwapExactAmountOutOutput):
        max_token_in = TokenAmount(symbol=contract_call['inputs']['tokenIn_symbol'], amount=contract_call['inputs']['maxAmountIn'])
        token_out = TokenAmount(symbol=contract_call['inputs']['tokenOut_symbol'], amount=contract_call['inputs']['tokenAmountOut'])
        swap_input = SwapExactAmountOutInput(max_token_in=max_token_in, token_out=token_out)
        swap_output = SwapExactAmountOutOutput(TokenAmount.ta_with_dict(action['token_in']))
        return swap_input, swap_output

    @staticmethod
    def exit_pool_simplified(action: dict) -> (ExitPoolInput, ExitPoolOutput):
        exit_input = ExitPoolInput(Decimal(action['pool_amount_in']))
        exit_output = ExitPoolOutput(list(map(lambda x: TokenAmount.ta_with_dict(x), action['tokens_out'])))
        return exit_input, exit_output

    @staticmethod
    def exit_pool_contract_call(action: dict, contract_call: dict) -> (ExitPoolInput, ExitPoolOutput):
        exit_input = ExitPoolInput(Decimal(contract_call['inputs']['poolAmountIn']))
        exit_output = ExitPoolOutput(list(map(lambda x: TokenAmount.ta_with_dict(x), action['tokens_out'])))
        return exit_input, exit_output

    @staticmethod
    def exit_swap_pool_amount_in_simplified(action: dict) -> (ExitSwapPoolAmountInInput, ExitSwapPoolAmountInOutput):
        exit_swap_input = ExitSwapPoolAmountInInput(action['inputs']['pool_amount_in'])
        exit_swap_output = ExitSwapPoolAmountInOutput(token_out=TokenAmount.ta_with_dict(action['token_out']))
        return exit_swap_input, exit_swap_output

    @staticmethod
    def exit_swap_pool_amount_in_contract_call(action: dict, contract_call: dict) -> (ExitSwapPoolAmountInInput, ExitSwapPoolAmountInOutput):
        exit_swap_input = ExitSwapPoolAmountInInput(contract_call['inputs']['poolAmountIn'])
        exit_swap_output = ExitSwapPoolAmountInOutput(token_out=TokenAmount.ta_with_dict(action['token_out']))
        return exit_swap_input, exit_swap_output

    @staticmethod
    def exit_swap_extern_amount_out_contract_call(action: dict, contract_call: dict) -> (ExitSwapPoolExternAmountOutInput, ExitSwapPoolExternAmountOutOutput):
        token_out = TokenAmount(symbol=contract_call['inputs']['tokenOut_symbol'], amount=contract_call['inputs']['tokenAmountOut'])
        exit_swap_input = ExitSwapPoolExternAmountOutInput(token_out=token_out, max_pool_in=Decimal(contract_call['inputs']['maxPoolAmountIn']))
        exit_swap_output = ExitSwapPoolExternAmountOutOutput(action['pool_amount_in'])
        return exit_swap_input, exit_swap_output











