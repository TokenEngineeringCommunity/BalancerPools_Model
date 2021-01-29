from decimal import Decimal
import ipdb
import pandas as pd

from model.parts.balancer_constants import (EXIT_FEE, MAX_IN_RATIO,
                                            MAX_OUT_RATIO)
from model.parts.balancer_math import BalancerMath

import pandas as pd


def calculate_total_denorm_weight(pool):
    total_weight = 0
    for asset in pool['tokens']:
        if pool['tokens'][asset]['bound']:
            total_weight += pool['tokens'][asset]['denorm_weight']
    return total_weight


class ActionDecoder:
    action_df = None

    @classmethod
    def load_actions(cls, path_to_action_file: str) -> int:
        ActionDecoder.action_df = pd.read_json(path_to_action_file).drop(0)
        return len(ActionDecoder.action_df)

    @staticmethod
    def p_action_decoder(params, step, history, current_state):
        if ActionDecoder.action_df is None:
            raise Exception('call ActionDecoder.load_actions(path_to_action.json) first')
        '''
        In this simplified model of Balancer, we have not modeled user behavior. Instead, we map events to actions.
        '''
        idx = current_state['timestep'] + 1
        action = ActionDecoder.action_df['action'][idx]
        if action['type'] == 'swap':
            answer = p_swap_exact_amount_in(params, step, history, current_state, action)
        elif action['type'] == 'join':
            answer = p_join_pool(params, step, history, current_state, action)
        elif action['type'] == 'join_swap':
            answer = p_join_swap_extern_amount_in(params, step, history, current_state, action)
        elif action['type'] == 'exit_swap':
            answer = p_exit_swap_extern_amount_out(params, step, history, current_state, action)
        elif action['type'] == 'external_price_update':
            return {'external_price_update': action['tokens'], 'change_datetime_update': action['datetime'], 'action_type': action['type']}
        else:
            raise Exception("Action type {} unimplemented".format(action['type']))
        return {'pool_update': answer, 'change_datetime_update': action['datetime'], 'action_type': action['type']}

def p_swap_exact_amount_in(params, step, history, current_state, action):
    pool = current_state['pool']
    # Parse action params
    token_in = action['token_in']
    token_amount_in = Decimal(str(action['token_amount_in']))
    token_out = action['token_out']
    min_pool_amount_out = pool['tokens'][token_in]
    swap_fee = pool['swap_fee']

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
        swap_fee=Decimal(swap_fee)
    )
    pool_in_balance = float(Decimal(min_pool_amount_out['balance']) + Decimal(token_amount_in))
    min_pool_amount_out['balance'] = pool_in_balance
    pool_out_balance = float(Decimal(out_record['balance']) - token_amount_out)
    out_record['balance'] = pool_out_balance

    return pool


def p_join_pool(params, step, history, current_state, action):
    """
    Join a pool by providing liquidity for all assets.
    """
    pool = current_state['pool']

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
            print("WARNING: calculated that user should get {} {} but input specified that he should get {} {} instead".format(amount, asset,
                                                                                                                               amount_expected,
                                                                                                                               asset))

        pool['tokens'][asset]['balance'] += amount
    pool['pool_shares'] += pool_amount_out

    return pool


def p_join_swap_extern_amount_in(params, step, history, current_state, action):
    """
    Join a pool by providing liquidity for a single asset.
    """
    pool = current_state['pool']
    tokens_in = action['tokens_in']
    pool_amount_out_expected = action['pool_amount_out']
    swap_fee = pool['swap_fee']

    total_weight = calculate_total_denorm_weight(pool)

    asset = list(tokens_in.keys())[0]
    amount = tokens_in[asset]
    pool_amount_out = BalancerMath.calc_pool_out_given_single_in(
        token_balance_in=Decimal(pool['tokens'][asset]['balance']),
        token_weight_in=pool['tokens'][asset]['denorm_weight'],
        pool_supply=Decimal(pool['pool_shares']),
        total_weight=Decimal(total_weight),
        token_amount_in=Decimal(amount),
        swap_fee=Decimal(swap_fee)
    )
    if pool_amount_out != pool_amount_out_expected:
        print(
            "WARNING: calculated that user should get {} pool shares but input specified that he should get {} pool shares instead".format(
                pool_amount_out, pool_amount_out_expected))

    pool['pool_shares'] += float(pool_amount_out)
    pool['tokens'][asset]['balance'] += float(amount)

    return pool


def p_exit_swap_extern_amount_out(params, step, history, current_state, action):
    """
    Exit a pool by withdrawing liquidity for a single asset.
    """
    pool = current_state['pool']
    swap_fee = pool['swap_fee']
    asset = list(action["tokens_out"].keys())[0]
    # Check that all tokens_out are bound
    if not pool['tokens'][asset]['bound']:
        raise Exception("ERR_NOT_BOUND")
    # Check that user is not trying to withdraw too many tokens
    if action["tokens_out"][asset] > Decimal(pool['tokens'][asset]['balance']) * MAX_OUT_RATIO:
        raise Exception("ERR_MAX_OUT_RATIO")

    total_weight = calculate_total_denorm_weight(pool)

    pool_amount_in = BalancerMath.calc_pool_in_given_single_out(
        token_balance_out=Decimal(pool['tokens'][asset]['balance']),
        token_weight_out=Decimal(pool['tokens'][asset]['denorm_weight']),
        pool_supply=Decimal(pool['pool_shares']),
        total_weight=total_weight,
        token_amount_out=Decimal(action["tokens_out"][asset]),
        swap_fee=Decimal(swap_fee)
    )

    if pool_amount_in == 0:
        raise Exception("ERR_MATH_APPROX")
    if pool_amount_in != action["pool_amount_in"]:
        print(
            "WARNING: calculated that pool should get {} pool shares but input specified that pool should get {} pool shares instead".format(
                pool_amount_in, action["pool_amount_in"]))

    # Decrease asset (give it to user)
    pool['tokens'][asset]['balance'] -= action["tokens_out"][asset]
    # Burn the user's incoming pool shares - exit fee
    exit_fee = pool_amount_in * EXIT_FEE
    pool['pool_shares'] -= float(pool_amount_in - exit_fee)

    return pool
