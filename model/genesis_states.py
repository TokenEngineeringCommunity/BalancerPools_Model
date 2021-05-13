"""
Model parameters.
"""
import typing
import json
from decimal import Decimal

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

    pool = initial_values['pool']
    spot_prices = {t: pool.spot_prices(t)[t] for t in pool.tokens}
    initial_values["spot_prices"] = spot_prices

    return initial_values
