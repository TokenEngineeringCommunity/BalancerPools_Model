import ipdb
from decimal import Decimal

from model.parts.balancer_constants import MAX_IN_RATIO
from model.parts.balancer_math import BalancerMath


def s_update_pool(params, substep, state_history, previous_state, policy_input):
    if policy_input['pool_update']['type'] == 'swap':
        return s_swap_exact_amount_in(params, substep, state_history, previous_state, policy_input)
    elif policy_input['pool_update']['type'] == 'join':
        return s_join_pool(params, substep, state_history, previous_state, policy_input)
    else:
        return 'pool', previous_state['pool'].copy()

def s_join_pool(params, substep, state_history, previous_state, policy_input):
    pool = previous_state['pool']
    # {'tokens': {'DAI': {'weight': 20, 'denorm_weight': 10, 'balance': 10396481.68700885, 'bound': True}, 'WETH': {'weight': 80, 'denorm_weight': 40, 'balance': 68684.50672373343, 'bound': True}}, 'generated_fees': 0.0, 'pool_shares': 100.0}

    action = policy_input['pool_update']
    # {'pool_update': {'pool_amount_out': 2.9508254125206002e-05, 'tokens_in': {'DAI': 2.95487676566492, 'WETH': 0.019993601301505}, 'type': 'join'}}
    # pool_amount_out = policy_input['pool_amount_out']

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
        pool['tokens'][asset]['balance'] += amount_expected
    pool['pool_shares'] += pool_amount_out

    return 'pool', pool

def s_join_swap_extern_amount_in(params, substep, state_history, previous_state, policy_input):
    pass

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
