"""
Model parameters.
"""
import typing
import json
from decimal import Decimal
# These are the initial conditions of the DAI-ETH Uniswap instance - https://etherscan.io/address/0x09cabEC1eAd1c0Ba254B09efb3EE13841712bE14

from model.models import Token
from model.parts.pool_state_updates import calculate_spot_prices, create_pool


def parse_initial_state(initial_values_json: str, spot_price_base_currency: str, gas_cost: Decimal) -> typing.Dict:
    with open(initial_values_json, "r") as f:
        initial_values = json.load(f, object_hook=token_finding_hook)
    # Figure out the tokens that are NOT the spot_price_base_currency
    pool = initial_values['pool']
    spot_prices = calculate_spot_prices(pool, ref_token=spot_price_base_currency)
    initial_values["spot_prices"] = spot_prices
    initial_values["gas_cost"] = gas_cost
    return initial_values


def generate_initial_state(token_symbols: typing.List[str],
                           tokens: typing.List[Token],
                           swap_fee: Decimal,
                           pool_shares: Decimal,
                           spot_price_base_currency: str,
                           token_prices: dict,
                           gas_cost: Decimal) -> typing.Dict:
    initial_values = {}
    # Figure out the tokens that are NOT the spot_price_base_currency
    pool = create_pool(token_symbols=token_symbols, tokens=tokens, swap_fee=swap_fee, pool_shares=pool_shares)
    initial_values["pool"] = pool
    spot_prices = calculate_spot_prices(pool, ref_token=spot_price_base_currency)
    initial_values["spot_prices"] = spot_prices
    initial_values["gas_cost"] = gas_cost
    if set(token_prices.keys()) != set(token_symbols):
        raise Exception('unexpected token prices')
    initial_values["token_prices"] = token_prices
    initial_values["action_type"] = "pool_creation"
    return initial_values


def token_finding_hook(k):
    if "weight" in k and "denorm_weight" in k and "balance" in k and "bound" in k:
        return Token(weight=k["weight"], denorm_weight=k["denorm_weight"], balance=Decimal(k["balance"]), bound=k["bound"])
    return k
