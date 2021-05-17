from decimal import Decimal

from attr import dataclass


@dataclass(repr=False)
class TokenAmount:
    symbol: str
    amount: Decimal

    @staticmethod
    def ta_with_dict(token_dict):
        return TokenAmount(symbol=token_dict['symbol'], amount=Decimal(token_dict['amount']))

    def __repr__(self):
        return f'{self.amount:.4f} {self.symbol}'

    def __mul__(self, other):
        if not isinstance(other, TokenAmount):
            raise ValueError("Other must be a TokenAmount as well")
        amount_new = self.amount * other.amount
        return TokenAmount(symbol=other.symbol, amount=amount_new)

    def __add__(self, other):
        if not isinstance(other, TokenAmount):
            raise ValueError("Other must be a TokenAmount as well")
        if other.symbol != self.symbol:
            raise ValueError("You really shouldn't add a {} and {} together".format(self.symbol, other.symbol))
        amount_new = self.amount + other.amount
        return TokenAmount(symbol=self.symbol, amount=amount_new)

    def __radd__(self, other):
        if other == 0:
            return self
        else:
            return self.__add__(other)
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
    pool_amount_out: Decimal
    max_token_in: TokenAmount

@dataclass
class JoinSwapPoolAmountOutOutput(object):
    token_in: TokenAmount

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
        join_input = JoinParamsInput(Decimal(action['pool_amount_out']), list(filter(lambda x: x['symbol'], tokens_in)))
        join_output = JoinParamsOutput(list(map(lambda x: TokenAmount.ta_with_dict(x), tokens_in)))
        return join_input, join_output

    @staticmethod
    def join_pool_contract_call(action: dict, contract_call: dict) -> (JoinParamsInput, JoinParamsOutput):
        tokens_in = action['tokens_in']
        join_input = JoinParamsInput(Decimal(contract_call['inputs']['poolAmountOut']), list(filter(lambda x: x['symbol'], tokens_in)))
        join_output = JoinParamsOutput(list(map(lambda x: TokenAmount.ta_with_dict(x), tokens_in)))
        return join_input, join_output

    @staticmethod
    def join_swap_extern_amount_in_simplified(action: dict) -> (JoinSwapExternAmountInInput, JoinSwapExternAmountInOutput):
        join_swap_input = JoinSwapExternAmountInInput(TokenAmount.ta_with_dict(action['token_in']))
        join_swap_output = JoinSwapExternAmountInOutput(Decimal(action['pool_amount_out']))
        return join_swap_input, join_swap_output

    @staticmethod
    def join_swap_extern_amount_in_contract_call(action: dict, contract_call: dict) -> (JoinSwapExternAmountInInput, JoinSwapExternAmountInOutput):
        join_swap_input = JoinSwapExternAmountInInput(TokenAmount(symbol=contract_call['inputs']['tokenIn_symbol'], amount=Decimal(contract_call['inputs']['tokenAmountIn'])))
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
        token_in = TokenAmount(symbol=contract_call['inputs']['tokenIn_symbol'], amount=Decimal(contract_call['inputs']['tokenAmountIn']))
        min_token_out = TokenAmount(symbol=contract_call['inputs']['tokenOut_symbol'], amount=Decimal(contract_call['inputs']['minAmountOut']))
        swap_input = SwapExactAmountInInput(token_in=token_in,
                                            min_token_out=min_token_out)
        swap_output = SwapExactAmountInOutput(TokenAmount.ta_with_dict(action['token_out']))
        return swap_input, swap_output

    @staticmethod
    def swap_exact_amount_out_contract_call(action: dict, contract_call: dict) -> (SwapExactAmountOutInput, SwapExactAmountOutOutput):
        max_token_in = TokenAmount(symbol=contract_call['inputs']['tokenIn_symbol'], amount=Decimal(contract_call['inputs']['maxAmountIn']))
        token_out = TokenAmount(symbol=contract_call['inputs']['tokenOut_symbol'], amount=Decimal(contract_call['inputs']['tokenAmountOut']))
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
        exit_swap_input = ExitSwapPoolAmountInInput(Decimal(action['pool_amount_in']))
        exit_swap_output = ExitSwapPoolAmountInOutput(token_out=TokenAmount.ta_with_dict(action['token_out']))
        return exit_swap_input, exit_swap_output

    @staticmethod
    def exit_swap_pool_amount_in_contract_call(action: dict, contract_call: dict) -> (ExitSwapPoolAmountInInput, ExitSwapPoolAmountInOutput):
        exit_swap_input = ExitSwapPoolAmountInInput(Decimal(contract_call['inputs']['poolAmountIn']))
        exit_swap_output = ExitSwapPoolAmountInOutput(token_out=TokenAmount.ta_with_dict(action['token_out']))
        return exit_swap_input, exit_swap_output

    @staticmethod
    def exit_swap_extern_amount_out_contract_call(action: dict, contract_call: dict) -> (ExitSwapPoolExternAmountOutInput, ExitSwapPoolExternAmountOutOutput):
        token_out = TokenAmount(symbol=contract_call['inputs']['tokenOut_symbol'], amount=Decimal(contract_call['inputs']['tokenAmountOut']))
        exit_swap_input = ExitSwapPoolExternAmountOutInput(token_out=token_out, max_pool_in=Decimal(contract_call['inputs']['maxPoolAmountIn']))
        exit_swap_output = ExitSwapPoolExternAmountOutOutput(Decimal(action['pool_amount_in']))
        return exit_swap_input, exit_swap_output
