from decimal import Decimal

from model.parts.balancer_constants import MAX_IN_RATIO
from model.parts.balancer_math import BalancerMath


def s_update_pool(params, substep, state_history, previous_state, policy_input):
    if policy_input['pool_update']['type'] == 'swap':
        return s_swap_exact_amount_in(params, substep, state_history, previous_state, policy_input)
    else:
        return 'pool', previous_state['pool'].copy()


def s_swap_exact_amount_in(params, substep, state_history, previous_state, policy_input):
    pool = previous_state['pool'].copy()

    # Parse action params
    action = policy_input['pool_update']
    token_in = action['token_in']
    token_amount_in = Decimal(str(action['token_amount_in']))
    token_out = action['token_out']
    min_pool_amount_out = pool['tokens'][token_in]
    # TODO plug param
    swap_fee = Decimal('0.1')

    if not min_pool_amount_out['bound']:
        raise Exception('ERR_NOT_BOUND')
    out_record = pool['tokens'][token_out]
    if not out_record['bound']:
        raise Exception('ERR_NOT_BOUND')

    if token_amount_in > Decimal(min_pool_amount_out['balance']) * MAX_IN_RATIO:
        raise Exception("ERR_MAX_IN_RATIO")

    token_amount_out = BalancerMath.calc_out_given_in(
        token_balance_in=Decimal(str(min_pool_amount_out['balance'])),
        token_weight_in=Decimal(str(min_pool_amount_out['denorm_weight'])),
        token_balance_out=Decimal(str(out_record['balance'])),
        token_weight_out=Decimal(str(out_record['denorm_weight'])),
        token_amount_in=token_amount_in,
        swap_fee=swap_fee
    )
    pool_in_balance = float(Decimal(min_pool_amount_out['balance']) + Decimal(token_amount_in))
    min_pool_amount_out['balance'] = pool_in_balance
    pool_out_balance = float(Decimal(out_record['balance']) - token_amount_out)
    out_record['balance'] = pool_out_balance

    return 'pool', pool
