"""
Model parameters.
"""
import typing
import json
from decimal import Decimal
# These are the initial conditions of the DAI-ETH Uniswap instance - https://etherscan.io/address/0x09cabEC1eAd1c0Ba254B09efb3EE13841712bE14

from model.parts.balancer_math import BalancerMath
from model.models import Token


def generate_initial_state(initial_values_json: str, spot_price_base_currency: str) -> typing.Dict:
    with open(initial_values_json, "r") as f:
        initial_values = json.load(f, object_hook=convert_to_token_class)
    # Figure out the tokens that are NOT the spot_price_base_currency
    other_tokens = [*initial_values['pool']['tokens'].keys()]
    other_tokens.remove(spot_price_base_currency)

    spot_prices = {}
    for t in other_tokens:
        base_token = initial_values['pool']['tokens'][spot_price_base_currency]
        other_token = initial_values['pool']['tokens'][t]

        spot_prices[t] = BalancerMath.calc_spot_price(token_balance_in=base_token.balance,
                                                      token_weight_in=Decimal(base_token.denorm_weight),
                                                      token_balance_out=other_token.balance,
                                                      token_weight_out=Decimal(other_token.denorm_weight),
                                                      swap_fee=Decimal(initial_values['pool']['swap_fee']))
    initial_values["spot_prices"] = spot_prices
    initial_values['pool']['pool_shares'] = Decimal(initial_values['pool']['pool_shares'])
    return initial_values


def convert_to_token_class(k):
    if "weight" in k and "denorm_weight" in k and "balance" in k and "bound" in k:
        return Token(weight=k["weight"], denorm_weight=k["denorm_weight"], balance=Decimal(k["balance"]), bound=k["bound"])
    return k
