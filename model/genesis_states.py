"""
Model parameters.
"""
import typing
import json
# These are the initial conditions of the DAI-ETH Uniswap instance - https://etherscan.io/address/0x09cabEC1eAd1c0Ba254B09efb3EE13841712bE14

from decimal import Decimal

from model.parts.balancer_math import BalancerMath

def generate_initial_state(initial_values_json: str, spot_price_base_currency: str) -> typing.Dict:
    with open(initial_values_json, "r") as f:
        initial_values = json.load(f)

    # Figure out the tokens that are NOT the spot_price_base_currency
    other_tokens = [*initial_values['pool']['tokens'].keys()]
    other_tokens.remove(spot_price_base_currency)

    spot_prices = {}
    for t in other_tokens:
        base_token = initial_values['pool']['tokens'][spot_price_base_currency]
        other_token = initial_values['pool']['tokens'][t]

        spot_prices[t] = BalancerMath.calc_spot_price(token_balance_in=Decimal(other_token['balance']),
                                                token_weight_in=Decimal(other_token['denorm_weight']),
                                                token_balance_out=Decimal(base_token['balance']),
                                                token_weight_out=Decimal(base_token['denorm_weight']),
                                                swap_fee=Decimal(initial_values['pool']['swap_fee']))
    initial_values["spot_prices"] = spot_prices
    return initial_values
