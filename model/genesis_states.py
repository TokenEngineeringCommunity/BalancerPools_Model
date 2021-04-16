"""
Model parameters.
"""
import typing
import json
from decimal import Decimal
# These are the initial conditions of the DAI-ETH Uniswap instance - https://etherscan.io/address/0x09cabEC1eAd1c0Ba254B09efb3EE13841712bE14

from model.parts.balancer_math import BalancerMath
from model.models import Token, Pool


def generate_initial_state(initial_values_json: str, spot_price_base_currency: str) -> typing.Dict:
    def customtypes_hook(k):
        if "__type__" in k and k["__type__"] == "Pool":
            return Pool(tokens=k["tokens"], generated_fees=k["generated_fees"], shares=Decimal(k["pool_shares"]), swap_fee=Decimal(k["swap_fee"]))
        if "__type__" in k and k["__type__"] == "Token":
            return Token(denorm_weight=Decimal(k["denorm_weight"]), balance=Decimal(k["balance"]), bound=k["bound"])
        return k

    with open(initial_values_json, "r") as f:
        initial_values = json.load(f, object_hook=customtypes_hook)
    # Figure out the tokens that are NOT the spot_price_base_currency
    other_tokens = initial_values["pool"].bound_tokens
    other_tokens.remove(spot_price_base_currency)

    spot_prices = {}
    for t in other_tokens:
        base_token = initial_values['pool'].tokens[spot_price_base_currency]
        other_token = initial_values['pool'].tokens[t]

        spot_prices[t] = BalancerMath.calc_spot_price(token_balance_in=base_token.balance,
                                                      token_weight_in=base_token.denorm_weight,
                                                      token_balance_out=other_token.balance,
                                                      token_weight_out=other_token.denorm_weight,
                                                      swap_fee=initial_values['pool'].swap_fee)
    initial_values["spot_prices"] = spot_prices
    return initial_values
