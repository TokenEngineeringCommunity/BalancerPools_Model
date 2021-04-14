import json
import typing
from decimal import Decimal
from model.parts.balancer_math import BalancerMath
from model.parts.balancer_constants import (EXIT_FEE, MAX_IN_RATIO,
                                            MAX_OUT_RATIO, MAX_BOUND_TOKENS, MIN_BALANCE, MIN_WEIGHT, MAX_WEIGHT, MAX_TOTAL_WEIGHT)
def ensure_type(value, types):
    if isinstance(value, types):
        return value
    else:
        raise TypeError('Value {value} is {value_type}, but should be {types}!'.format(
            value=value, value_type=type(value), types=types))

class Token:
    def __init__(self, weight: Decimal, denorm_weight: Decimal, balance: Decimal, bound: bool):
        self.weight = weight
        self.denorm_weight = denorm_weight
        self.balance = balance
        self.bound = bound

    def __repr__(self):
        return "<Token weight: {}, denorm_weight: {}, balance: {}, bound: {}>".format(self.weight, self.denorm_weight, self.balance, self.bound)

    def __eq__(self, other):
        if isinstance(other, Token):
            return (self.weight == other.weight) and (self.denorm_weight == other.denorm_weight) and (self.balance == other.balance) and (self.bound == other.bound)
        return NotImplemented

    def add(self, num):
        self.amount = self.amount + num
        return self.amount

    @property
    def balance(self):
        return self.__dict__['balance']

    @balance.setter
    def balance(self, value):
        self.__dict__['balance'] = ensure_type(value, Decimal)

class Pool:
    def __init__(self, tokens: typing.Dict, generated_fees: typing.Dict, shares: Decimal, swap_fee: Decimal):
        self.tokens = tokens
        self.generated_fees = generated_fees
        self.shares = Decimal(shares)
        self.swap_fee = Decimal(swap_fee)

    # @staticmethod
    # def fromJSON(path: str):
    #     with open(path, "r") as f:

    def toJSON(self):
        return json.dumps(self.as_dict())

    def as_dict(self):
        return self.__dict__

    def spot_prices(self, ref_token: str):
        balance_in = self.tokens[ref_token].balance
        weight_in = self.tokens[ref_token].weight
        spot_prices = {}
        for token in self.tokens:
            if token == ref_token:
                continue
            balance_out = self.tokens[token].balance
            weight_out = self.tokens[token].weight

            price = BalancerMath.calc_spot_price(token_balance_in=Decimal(balance_in),
                                                token_weight_in=Decimal(weight_in),
                                                token_balance_out=Decimal(balance_out),
                                                token_weight_out=Decimal(weight_out),
                                                swap_fee=self.swap_fee)
            spot_prices[token] = price
        return spot_prices

    @property
    def total_denorm_weight(self):
        total_weight = Decimal('0')
        for token_symbol in self.tokens:
            if self.tokens[token_symbol].bound:
                total_weight += Decimal(self.tokens[token_symbol].denorm_weight)
        return total_weight

    @property
    def bound_tokens(self):
        return [token_symbol for token_symbol in self.tokens if self.tokens[token_symbol].bound]

    @property
    def balances(self):
        """
        INPUT: "pool": {"tokens": {"DAI": {"weight": "0.2", "denorm_weight": "10",
            "balance": "10000000", "bound": true
                },
                "WETH": {
                    "weight": "0.8",
                    "denorm_weight": "40",
                    "balance": "67738.636173102396002749",
                    "bound": true
                }
            },

        OUTPUT: {'DAI': Decimal('10011861.328308360999600128'), 'WETH':
        Decimal('67718.61443839753075637013346')}
        """
        ans = {}
        for t in self.bound_tokens:
            ans[t] = self.tokens[t].balance
        return ans

    def bind(self, token_symbol: str, token: Token) -> Decimal:
        if self.tokens.get(token_symbol) is not None and self.tokens.get(token_symbol).bound is True:
            raise Exception('ERR_IS_BOUND')
        if len(list(self.tokens.keys())) >= MAX_BOUND_TOKENS:
            raise Exception("ERR_MAX_TOKENS")
        token.bound = True
        self.tokens[token_symbol] = token
        return self.rebind(token_symbol, token)

    def rebind(self, token_symbol: str, token: Token) -> Decimal:
        if self.tokens.get(token_symbol) is None or self.tokens.get(token_symbol).bound is False:
            raise Exception("ERR_NOT_BOUND")
        if token.denorm_weight < MIN_WEIGHT:
            raise Exception("ERR_MIN_WEIGHT")
        if token.denorm_weight > MAX_WEIGHT:
            raise Exception("ERR_MAX_WEIGHT")
        if token.balance < MIN_BALANCE:
            raise Exception("ERR_MIN_BALANCE")
        old_weight = self.tokens[token_symbol].denorm_weight
        print('total_denorm', self.total_denorm_weight)
        if token.denorm_weight > old_weight:
            total_denorm_weight_new = self.total_denorm_weight + (token.denorm_weight - old_weight)
            print('total_denorm >', total_denorm_weight_new)
            if total_denorm_weight_new > MAX_TOTAL_WEIGHT:
                raise Exception("ERR_MAX_TOTAL_WEIGHT")
        elif token.denorm_weight < old_weight:
            print('total_denorm <', self.total_denorm_weight)
        self.tokens[token_symbol].denorm_weight = token.denorm_weight

        old_balance = self.tokens[token_symbol].balance
        self.tokens[token_symbol].balance = token.balance
        for ts in self.tokens.keys():
            if self.total_denorm_weight == Decimal('0'):
                self.tokens[ts].weight = 1.0
            else:
                self.tokens[ts].weight = self.tokens[ts].denorm_weight / self.total_denorm_weight
        if token.balance > old_balance:
            return - (token.balance - old_balance)
        elif token.balance < old_balance:
            token_balance_withdrawn = old_balance - token.balance
            return token_balance_withdrawn

    def unbind(self, token_symbol: str) -> dict:
        if self.tokens.get(token_symbol) is None or self.tokens.get(token_symbol).bound is False:
            raise Exception("ERR_NOT_BOUND")

        token_removed = self.tokens.pop(token_symbol)
        return {token_symbol: token_removed.balance}

    @property
    def shares(self):
        return self.__dict__['shares']

    @shares.setter
    def shares(self, value):
        self.__dict__['shares'] = ensure_type(value, Decimal)

    @property
    def swap_fee(self):
        return self.__dict__['swap_fee']

    @swap_fee.setter
    def swap_fee(self, value):
        self.__dict__['swap_fee'] = ensure_type(value, Decimal)

    def __repr__(self):
        return f"<Pool tokens: {self.tokens} generated_fees: {self.generated_fees} shares: {self.shares} swap_fee: {self.swap_fee} >"
