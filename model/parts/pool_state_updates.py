import ipdb
from decimal import Decimal

from model.parts.balancer_constants import MAX_IN_RATIO
from model.parts.balancer_math import BalancerMath


def s_update_pool(params, substep, state_history, previous_state, policy_input):
    if policy_input['pool_update']['type'] == 'swap':
        return s_swap_exact_amount_in(params, substep, state_history, previous_state, policy_input)
    elif policy_input['pool_update']['type'] == 'join':
        return s_join_pool(params, substep, state_history, previous_state, policy_input)
    elif policy_input['pool_update']['type'] == 'join_swap':
        return s_join_swap_extern_amount_in(params, substep, state_history, previous_state, policy_input)
    else:
        return 'pool', previous_state['pool'].copy()

def s_join_pool(params, substep, state_history, previous_state, policy_input):
    """
    Join a pool by providing liquidity for all assets.
    """
    pool = previous_state['pool']
    action = policy_input['pool_update']

    # tokens_in is a suggestion. The real fixed input is pool_amount_out - how many pool shares does the user want.
    # tokens_in will then be recalculated and that value used instead.
    tokens_in = action['tokens_in']
    pool_amount_out = action['pool_amount_out']

    ratio = pool_amount_out / pool['pool_shares']
    if ratio == 0:
        raise Exception("ERR_MATH_APPROX")

    for asset, amount_expected in tokens_in.items():
        amount = ratio * pool['tokens'][asset]['balance']
        if amount != amount_expected:
            print("WARNING: calculated that user should get {} {} but input specified that he should get {} {} instead".format(amount, asset, amount_expected, asset))
        pool['tokens'][asset]['balance'] += amount
    pool['pool_shares'] += pool_amount_out

    return 'pool', pool

def s_join_swap_extern_amount_in(params, substep, state_history, previous_state, policy_input):
    """
    Join a pool by providing liquidity for a single asset.
    """
    pool = previous_state['pool']
    action = policy_input['pool_update']
    tokens_in = action['tokens_in']
    pool_amount_out_expected = action['pool_amount_out']
    swap_fee = Decimal('0.1')

    total_weight = 0
    for asset in pool['tokens']:
        total_weight += pool['tokens'][asset]['denorm_weight']

    asset = list(tokens_in.keys())[0]
    amount = tokens_in[asset]
    pool_amount_out = BalancerMath.calc_pool_out_given_single_in(
        token_balance_in=Decimal(pool['tokens'][asset]['balance']),
        token_weight_in=pool['tokens'][asset]['denorm_weight'],
        pool_supply=Decimal(pool['pool_shares']),
        total_weight=Decimal(total_weight),
        token_amount_in=Decimal(amount),
        swap_fee=swap_fee
    )
    if pool_amount_out != pool_amount_out_expected:
        print("WARNING: calculated that user should get {} pool shares but input specified that he should get {} pool shares instead".format(pool_amount_out, pool_amount_out_expected))

    pool['pool_shares'] += float(pool_amount_out)
    pool['tokens'][asset]['balance'] += float(amount)

    return 'pool', pool

def s_exit_swap_extern_amount_out(params, substep, state_history, previous_state, policy_input):
    pass

def s_swap_exact_amount_in(params, substep, state_history, previous_state, policy_input):
    pool = previous_state['pool']

    # Parse action params
    action = policy_input['pool_update']
    token_in = action['token_in']
    token_amount_in = Decimal(str(action['token_amount_in']))
    token_out = action['token_out']
    min_pool_amount_out = pool['tokens'][token_in]
    # TODO fee as system param
    swap_fee = Decimal('0.1')

    # ipdb.set_trace()
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
