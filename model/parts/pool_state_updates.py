from decimal import Decimal

from model.parts.balancer_math import BalancerMath


def s_update_pool(params, substep, state_history, previous_state, policy_input):
    pool = policy_input.get('pool_update')
    if pool is None:
        return 'pool', previous_state['pool']
    return 'pool', pool


def calculate_spot_prices(pool: dict, ref_token: str, ):
    swap_fee = pool['swap_fee']
    balance_out = pool['tokens'][ref_token]['balance']
    weight_out = pool['tokens'][ref_token]['weight']
    spot_prices = {}
    for token in pool['tokens']:
        if token == ref_token:
            continue
        balance_in = pool['tokens'][ref_token]['balance']
        weight_in = pool['tokens'][ref_token]['weight']

        price = BalancerMath.calc_spot_price(token_balance_in=Decimal(balance_in),
                                             token_weight_in=Decimal(weight_in),
                                             token_balance_out=Decimal(balance_out),
                                             token_weight_out=Decimal(weight_out),
                                             swap_fee=Decimal(swap_fee))
        spot_prices[token] = price
    return spot_prices


def s_update_spot_prices(params, substep, state_history, previous_state, policy_input):
    pool = policy_input.get('pool_update')
    if pool is None:
        return 'spot_prices', previous_state['spot_prices']

    ref_token = params[0]['spot_price_reference']

    spot_prices = calculate_spot_prices(pool, ref_token)

    return 'spot_prices', spot_prices
