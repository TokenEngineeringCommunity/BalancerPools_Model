from decimal import Decimal
# import ipdb
import pandas as pd

from model.parts.balancer_constants import (EXIT_FEE, MAX_IN_RATIO,
                                            MAX_OUT_RATIO)
from model.parts.balancer_math import BalancerMath

import pandas as pd


def calculate_total_denorm_weight(pool) -> Decimal:
    total_weight = Decimal('0')
    for token_symbol in pool['tokens']:
        if pool['tokens'][token_symbol].bound:
            total_weight += Decimal(pool['tokens'][token_symbol].denorm_weight)
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
        timestamp = ActionDecoder.action_df['timestamp'][idx]
        if action['type'] == 'swap':
            answer = p_swap_exact_amount_in(params, step, history, current_state, action)
        elif action['type'] == 'join':
            answer = p_join_pool(params, step, history, current_state, action)
        elif action['type'] == 'join_swap':
            answer = p_join_swap_extern_amount_in(params, step, history, current_state, action)
        elif action['type'] == 'exit_swap':
            answer = p_exit_swap_extern_amount_out(params, step, history, current_state, action)
        elif action['type'] == 'exit':
            answer = p_exit_pool(params, step, history, current_state, action)
        elif action['type'] == 'external_price_update':
            return {'external_price_update': action['tokens'], 'change_datetime_update': timestamp, 'action_type': action['type']}
        else:
            raise Exception("Action type {} unimplemented".format(action['type']))
        return {'pool_update': answer, 'change_datetime_update': timestamp, 'action_type': action['type']}


def p_swap_exact_amount_in(params, step, history, current_state, action):
    pool = current_state['pool']
    # Parse action params
    token_in_symbol = action['token_in']['symbol']
    token_amount_in = Decimal(action['token_in']['amount'])
    token_out = action['token_out']['symbol']
    pool_token_in = pool['tokens'][token_in_symbol]
    swap_fee = pool['swap_fee']

    if not pool_token_in.bound:
        raise Exception('ERR_NOT_BOUND')
    out_record = pool['tokens'][token_out]
    if not out_record.bound:
        raise Exception('ERR_NOT_BOUND')

    if token_amount_in > Decimal(pool_token_in.balance) * MAX_IN_RATIO:
        raise Exception("ERR_MAX_IN_RATIO")

    swap_result = BalancerMath.calc_out_given_in(
        token_balance_in=pool_token_in.balance,
        token_weight_in=Decimal(str(pool_token_in.denorm_weight)),
        token_balance_out=out_record.balance,
        token_weight_out=Decimal(str(out_record.denorm_weight)),
        token_amount_in=token_amount_in,
        swap_fee=Decimal(swap_fee)
    )

    generated_fees = pool['generated_fees']
    generated_fees[token_in_symbol] = Decimal(generated_fees[token_in_symbol]) + swap_result.fee

    pool_in_balance = pool_token_in.balance + token_amount_in
    pool_token_in.balance = pool_in_balance
    pool_out_balance = out_record.balance - swap_result.result
    out_record.balance = pool_out_balance

    return pool


def p_join_pool(params, step, history, current_state, action):
    """
    Join a pool by providing liquidity for all token_symbols.
    """
    pool = current_state['pool']

    # tokens_in is a suggestion. The real fixed input is pool_amount_out - how many pool shares does the user want.
    # tokens_in will then be recalculated and that value used instead.
    tokens_in = action['tokens_in']
    pool_amount_out = Decimal(action['pool_amount_out'])

    ratio = pool_amount_out / Decimal(pool['pool_shares'])
    if ratio == Decimal('0'):
        raise Exception("ERR_MATH_APPROX")

    for token in tokens_in:
        amount_expected = token['amount']
        symbol = token['symbol']
        amount = ratio * pool['tokens'][symbol].balance
        if amount != amount_expected:
            print("WARNING: calculated that user should get {} {} but input specified that he should get {} {} instead".format(amount, symbol,
                                                                                                                               amount_expected,
                                                                                                                               symbol))
        pool['tokens'][symbol].balance += amount
    pool['pool_shares'] += pool_amount_out

    return pool


def p_join_swap_extern_amount_in(params, step, history, current_state, action):
    """
    Join a pool by providing liquidity for a single token_symbol.
    """
    pool = current_state['pool']
    tokens_in_symbol = action['token_in']['symbol']
    token_in_amount = Decimal(action['token_in']['amount'])
    pool_amount_out_expected = Decimal(action['pool_amount_out'])
    swap_fee = pool['swap_fee']

    total_weight = calculate_total_denorm_weight(pool)

    join_swap = BalancerMath.calc_pool_out_given_single_in(
        token_balance_in=Decimal(pool['tokens'][tokens_in_symbol].balance),
        token_weight_in=Decimal(pool['tokens'][tokens_in_symbol].denorm_weight),
        pool_supply=Decimal(pool['pool_shares']),
        total_weight=Decimal(total_weight),
        token_amount_in=Decimal(token_in_amount),
        swap_fee=Decimal(swap_fee)
    )
    generated_fees = pool['generated_fees']
    generated_fees[tokens_in_symbol] = Decimal(generated_fees[tokens_in_symbol]) + join_swap.fee

    pool_amount_out = join_swap.result
    if pool_amount_out != pool_amount_out_expected:
        print(
            "WARNING: calculated that user should get {} pool shares but input specified that he should get {} pool shares instead.".format(
                pool_amount_out, pool_amount_out_expected))

    pool['pool_shares'] = Decimal(pool['pool_shares']) + pool_amount_out
    pool['tokens'][tokens_in_symbol].balance += token_in_amount

    return pool


def p_exit_swap_extern_amount_out(params, step, history, current_state, action):
    """
    Exit a pool by withdrawing liquidity for a single token_symbol.
    """
    pool = current_state['pool']
    swap_fee = pool['swap_fee']
    token_out_symbol = action['token_out']['symbol']
    # Check that all tokens_out are bound
    if not pool['tokens'][token_out_symbol].bound:
        raise Exception("ERR_NOT_BOUND")
    # Check that user is not trying to withdraw too many tokens
    token_amount_out = Decimal(action['token_out']['amount'])
    if token_amount_out > Decimal(pool['tokens'][token_out_symbol].balance) * MAX_OUT_RATIO:
        raise Exception("ERR_MAX_OUT_RATIO")

    total_weight = calculate_total_denorm_weight(pool)

    exit_swap = BalancerMath.calc_pool_in_given_single_out(
        token_balance_out=Decimal(pool['tokens'][token_out_symbol].balance),
        token_weight_out=Decimal(pool['tokens'][token_out_symbol].denorm_weight),
        pool_supply=Decimal(pool['pool_shares']),
        total_weight=Decimal(total_weight),
        token_amount_out=token_amount_out,
        swap_fee=Decimal(swap_fee)
    )
    pool_amount_in = exit_swap.result
    
    generated_fees = pool['generated_fees']
    generated_fees[token_out_symbol] = Decimal(generated_fees[token_out_symbol]) + exit_swap.fee

    if pool_amount_in == 0:
        raise Exception("ERR_MATH_APPROX")
    if pool_amount_in != action["pool_amount_in"]:
        print(
            "WARNING: calculated that pool should get {} pool shares but input specified that pool should get {} pool shares instead".format(
                pool_amount_in, action["pool_amount_in"]))

    # Decrease token_symbol (give it to user)
    pool['tokens'][token_out_symbol].balance -= token_amount_out
    # Burn the user's incoming pool shares - exit fee
    exit_fee = pool_amount_in * EXIT_FEE
    pool['pool_shares'] = Decimal(pool['pool_shares']) - pool_amount_in - exit_fee

    return pool


def p_exit_pool(params, step, history, current_state, action):
    """
        Exit a pool by withdrawing liquidity for all token_symbol.
    """
    pool = current_state['pool']
    pool_shares = Decimal(pool['pool_shares'])
    pool_amount_in = Decimal(action['pool_amount_in'])

    # Current Balancer implementation has 0 exit fees, but we are leaving this to generalize
    exit_fee = pool_amount_in * Decimal(EXIT_FEE)
    pool_amount_in_afer_exit_fee = pool_amount_in - exit_fee
    ratio = pool_amount_in_afer_exit_fee / pool_shares

    pool['pool_shares'] = pool_shares - pool_amount_in_afer_exit_fee

    for token_symbol in pool['tokens']:
        token_amount_out = ratio * pool['tokens'][token_symbol].balance
        if token_amount_out == Decimal('0'):
            raise Exception("ERR_MATH_APPROX")
        pool['tokens'][token_symbol].balance -= token_amount_out

    return pool
