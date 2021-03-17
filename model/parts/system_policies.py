import typing
from decimal import Decimal, getcontext
# import ipdb
from enum import Enum

import pandas as pd
from attr import dataclass

from model.parts.balancer_constants import (EXIT_FEE, MAX_IN_RATIO,
                                            MAX_OUT_RATIO)
from model.parts.balancer_math import BalancerMath

import pandas as pd

from model.parts.pool_method_entities import JoinParamsInput, JoinParamsOutput, PoolMethodParamsDecoder, JoinSwapExternAmountInInput, \
    JoinSwapExternAmountInOutput, SwapExactAmountInInput, SwapExactAmountInOutput, SwapExactAmountOutInput, SwapExactAmountOutOutput, ExitPoolInput, \
    ExitPoolOutput, ExitSwapPoolAmountInInput, ExitSwapPoolAmountInOutput, ExitSwapPoolExternAmountOutInput, ExitSwapPoolExternAmountOutOutput, \
    JoinSwapPoolAmountOutOutput, JoinSwapPoolAmountOutInput

VERBOSE = False

getcontext().prec = 28

def update_fee(token_symbol: str, fee: Decimal, pool: dict) -> typing.Dict:
    generated_fees = pool['generated_fees'].copy()
    for token in generated_fees:
        if token == token_symbol:
            generated_fees[token] = fee
        else:
            generated_fees[token] = Decimal('0')

    return generated_fees


def calculate_total_denorm_weight(pool) -> Decimal:
    total_weight = Decimal('0')
    for token_symbol in pool['tokens']:
        if pool['tokens'][token_symbol].bound:
            total_weight += Decimal(pool['tokens'][token_symbol].denorm_weight)
    return total_weight


class ActionDecodingType(Enum):
    simplified = "SIMPLIFIED"
    contract_call = "CONTRACT_CALL"
    replay_output = "REPLAY_OUTPUT"


class ActionDecoder:
    action_df = None
    decoding_type = ActionDecodingType.simplified

    @classmethod
    def load_actions(cls, path_to_action_file: str) -> int:
        ActionDecoder.action_df = pd.read_json(path_to_action_file).drop(0)
        return len(ActionDecoder.action_df)

    @staticmethod
    def p_simplified_action_decoder(idx, params, step, history, current_state):
        action = ActionDecoder.action_df['action'][idx]
        timestamp = ActionDecoder.action_df['timestamp'][idx]
        tx_hash = ActionDecoder.action_df['tx_hash'][idx]
        if action['type'] == 'swap':
            input_params, output_params = PoolMethodParamsDecoder.swap_exact_amount_in_simplified(action)
            answer = p_swap_exact_amount_in(params, step, history, current_state, input_params, output_params)
        elif action['type'] == 'join':
            input_params, output_params = PoolMethodParamsDecoder.join_pool_simplified(action)
            answer = p_join_pool(params, step, history, current_state, input_params, output_params)
        elif action['type'] == 'join_swap':
            input_params, output_params = PoolMethodParamsDecoder.join_swap_extern_amount_in_simplified(action)
            answer = p_join_swap_extern_amount_in(params, step, history, current_state, input_params, output_params)
        elif action['type'] == 'exit_swap':
            input_params, output_params = PoolMethodParamsDecoder.exit_swap_pool_amount_in_simplified(action)
            answer = p_exit_swap_pool_amount_in(params, step, history, current_state, input_params, output_params)
        elif action['type'] == 'exit':
            input_params, output_params = PoolMethodParamsDecoder.exit_pool_simplified(action)
            answer = p_exit_pool(params, step, history, current_state, input_params, output_params)
        elif action['type'] == 'external_price_update':
            update_fee(token_symbol='', fee=Decimal('0'), pool=current_state['pool'])
            return {'external_price_update': action['tokens'], 'change_datetime_update': timestamp, 'action_type': action['type'],
                    'pool_update': current_state['pool']}
        else:
            raise Exception("Action type {} unimplemented".format(action['type']))
        return {'pool_update': answer, 'change_datetime_update': timestamp, 'action_type': action['type']}

    @staticmethod
    def p_contract_call_action_decoder(idx, params, step, history, current_state):
        action = ActionDecoder.action_df['action'][idx]
        timestamp = ActionDecoder.action_df['timestamp'][idx]
        tx_hash = ActionDecoder.action_df['tx_hash'][idx]
        contract_call = None
        if action['type'] != 'external_price_update':
            contract_call = ActionDecoder.action_df['contract_call'][idx][0]
        else:
            update_fee(token_symbol='', fee=Decimal('0'), pool=current_state['pool'])
            return {'external_price_update': action['tokens'], 'change_datetime_update': timestamp, 'action_type': action['type'],
                    'pool_update': current_state['pool']}
        if contract_call['type'] == 'joinswapExternAmountIn':
            input_params, output_params = PoolMethodParamsDecoder.join_swap_extern_amount_in_contract_call(action, contract_call)
            answer = p_join_swap_extern_amount_in(params, step, history, current_state, input_params, output_params)
        elif contract_call['type'] == 'joinPool':
            input_params, output_params = PoolMethodParamsDecoder.join_pool_contract_call(action, contract_call)
            answer = p_join_pool(params, step, history, current_state, input_params, output_params)
        elif contract_call['type'] == 'swapExactAmountIn':
            input_params, output_params = PoolMethodParamsDecoder.swap_exact_amount_in_contract_call(action, contract_call)
            answer = p_swap_exact_amount_in(params, step, history, current_state, input_params, output_params)
        elif contract_call['type'] == 'swapExactAmountOut':
            input_params, output_params = PoolMethodParamsDecoder.swap_exact_amount_out_contract_call(action, contract_call)
            answer = p_swap_exact_amount_out(params, step, history, current_state, input_params, output_params)
        elif contract_call['type'] == 'exitPool':
            input_params, output_params = PoolMethodParamsDecoder.exit_pool_contract_call(action, contract_call)
            answer = p_exit_pool(params, step, history, current_state, input_params, output_params)
        elif contract_call['type'] == 'exitswapPoolAmountIn':
            input_params, output_params = PoolMethodParamsDecoder.exit_swap_pool_amount_in_contract_call(action, contract_call)
            answer = p_exit_swap_pool_amount_in(params, step, history, current_state, input_params, output_params)
        elif contract_call['type'] == 'exitswapExternAmountOut':
            input_params, output_params = PoolMethodParamsDecoder.exit_swap_extern_amount_out_contract_call(action, contract_call)
            answer = p_exit_swap_extern_amount_out(params, step, history, current_state, input_params, output_params)
        else:
            raise Exception("Action type {} unimplemented".format(action['type']))
        return {'pool_update': answer, 'change_datetime_update': timestamp, 'action_type': action['type']}

    @staticmethod
    def p_plot_output_action_decoder(idx, params, step, history, current_state):
        action = ActionDecoder.action_df['action'][idx]
        timestamp = ActionDecoder.action_df['timestamp'][idx]
        if action['type'] == 'swap':
            input_params, output_params = PoolMethodParamsDecoder.swap_exact_amount_in_simplified(action)
            answer = p_swap_plot_output(params, step, history, current_state, input_params, output_params)
        elif action['type'] == 'join':
            input_params, output_params = PoolMethodParamsDecoder.join_pool_simplified(action)
            answer = p_join_pool_plot_output(params, step, history, current_state, input_params, output_params)
        elif action['type'] == 'join_swap':
            input_params, output_params = PoolMethodParamsDecoder.join_swap_extern_amount_in_simplified(action)
            answer = p_join_swap_plot_output(params, step, history, current_state, input_params, output_params)
        elif action['type'] == 'exit_swap':
            input_params, output_params = PoolMethodParamsDecoder.exit_swap_pool_amount_in_simplified(action)
            answer = p_exit_swap_plot_output(params, step, history, current_state, input_params, output_params)
        elif action['type'] == 'exit':
            input_params, output_params = PoolMethodParamsDecoder.exit_pool_simplified(action)
            answer = p_exit_pool_plot_output(params, step, history, current_state, input_params, output_params)
        elif action['type'] == 'external_price_update':
            update_fee(token_symbol='', fee=Decimal('0'), pool=current_state['pool'])
            return {'external_price_update': action['tokens'], 'change_datetime_update': timestamp, 'action_type': action['type'], 'pool_update': current_state['pool']}
        else:
            raise Exception("Action type {} unimplemented".format(action['type']))
        return {'pool_update': answer, 'change_datetime_update': timestamp, 'action_type': action['type']}

    @staticmethod
    def p_action_decoder(params, step, history, current_state):
        if ActionDecoder.action_df is None:
            raise Exception('call ActionDecoder.load_actions(path_to_action.json) first')
        '''
        In this simplified model of Balancer, we have not modeled user behavior. Instead, we map events to actions.
        '''
        # When only 1 param this happens
        if isinstance(params, list):
            # 1 param
            decoding_type = params[0]['decoding_type']
        else:
            # Parameter sweep
            decoding_type = params['decoding_type']

        ActionDecoder.decoding_type = ActionDecodingType(decoding_type)
        idx = current_state['timestep'] + 1
        if ActionDecoder.decoding_type == ActionDecodingType.simplified:
            return ActionDecoder.p_simplified_action_decoder(idx, params, step, history, current_state)
        elif ActionDecoder.decoding_type == ActionDecodingType.contract_call:
            return ActionDecoder.p_contract_call_action_decoder(idx, params, step, history, current_state)
        elif ActionDecoder.decoding_type == ActionDecodingType.replay_output:
            return ActionDecoder.p_plot_output_action_decoder(idx, params, step, history, current_state)
        else:
            raise Exception(f'unknwon decoding type {decoding_type}')


def p_swap_exact_amount_in(params, step, history, current_state, input_params: SwapExactAmountInInput,
                           output_params: SwapExactAmountInOutput) -> dict:
    pool = current_state['pool'].copy()
    # Parse action params
    token_in_symbol = input_params.token_in.symbol
    token_amount_in = input_params.token_in.amount
    token_out = input_params.min_token_out.symbol
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
        token_weight_in=Decimal(pool_token_in.denorm_weight),
        token_balance_out=out_record.balance,
        token_weight_out=Decimal(out_record.denorm_weight),
        token_amount_in=token_amount_in,
        swap_fee=Decimal(swap_fee)
    )

    pool["generated_fees"] = update_fee(token_in_symbol, swap_result.fee, pool)
    pool_in_balance = pool_token_in.balance + token_amount_in
    pool_token_in.balance = pool_in_balance
    pool_out_balance = out_record.balance - swap_result.result
    out_record.balance = pool_out_balance
    return pool


def p_swap_plot_output(params, step, history, current_state, input_params: SwapExactAmountInInput,
                       output_params: SwapExactAmountInOutput) -> dict:
    pool = current_state['pool'].copy()
    pool_token_in = pool['tokens'][input_params.token_in.symbol]
    pool_token_out = pool['tokens'][output_params.token_out.symbol]

    pool_token_in.balance = pool_token_in.balance + input_params.token_in.amount
    pool_token_out.balance = pool_token_out.balance - output_params.token_out.amount
    return pool


def p_swap_exact_amount_out(params, step, history, current_state, input_params: SwapExactAmountOutInput,
                            output_params: SwapExactAmountOutOutput) -> dict:
    pool = current_state['pool'].copy()
    # Parse action params
    token_in_symbol = input_params.max_token_in.symbol
    token_amount_out = input_params.token_out.amount
    token_out_symbol = input_params.token_out.symbol
    pool_token_out = pool['tokens'][token_out_symbol]
    pool_token_in = pool['tokens'][token_in_symbol]
    swap_fee = pool['swap_fee']

    if not pool_token_out.bound:
        raise Exception('ERR_NOT_BOUND')
    if not pool_token_in.bound:
        raise Exception('ERR_NOT_BOUND')
    if token_amount_out > (pool_token_out.balance * MAX_OUT_RATIO):
        raise Exception("ERR_MAX_OUT_RATIO")

    swap_result = BalancerMath.calc_in_given_out(
        token_balance_in=Decimal(pool_token_in.balance),
        token_weight_in=Decimal(pool_token_in.denorm_weight),
        token_balance_out=Decimal(pool_token_out.balance),
        token_weight_out=Decimal(pool_token_out.denorm_weight),
        token_amount_out=token_amount_out,
        swap_fee=Decimal(swap_fee)
    )
    token_amount_in = swap_result.result
    if token_amount_in > input_params.max_token_in.amount and VERBOSE:
        # raise Exception('ERR_LIMIT_IN')
        print(f"WARNING: token_amount_in {token_amount_in} > max {input_params.max_token_in.amount}")

    pool["generated_fees"] = update_fee(token_in_symbol, swap_result.fee, pool)

    pool_token_in.balance = pool_token_in.balance + token_amount_in
    pool_token_out.balance = pool_token_out.balance - token_amount_out

    return pool


def p_join_pool(params, step, history, current_state, input_params: JoinParamsInput, output_params: JoinParamsOutput) -> dict:
    """
    Join a pool by providing liquidity for all token_symbols.
    """
    pool = current_state['pool'].copy()

    # tokens_in is a suggestion. The real fixed input is pool_amount_out - how many pool shares does the user want.
    # tokens_in will then be recalculated and that value used instead.
    pool_amount_out = input_params.pool_amount_out

    ratio = pool_amount_out / Decimal(pool['pool_shares'])
    if ratio == Decimal('0'):
        raise Exception("ERR_MATH_APPROX")

    for token in output_params.tokens_in:
        amount_expected = token.amount
        symbol = token.symbol
        amount = ratio * pool['tokens'][symbol].balance
        if amount != amount_expected and VERBOSE:
            print("WARNING: calculated that user should get {} {} but input specified that he should get {} {} instead".format(amount, symbol,
                                                                                                                               amount_expected,
                                                                                                                               symbol))
        pool['tokens'][symbol].balance += amount
    pool['pool_shares'] += pool_amount_out

    return pool


def p_join_swap_extern_amount_in(params, step, history, current_state, input_params: JoinSwapExternAmountInInput,
                                 output_params: JoinSwapExternAmountInOutput) -> dict:
    """
    Join a pool by providing liquidity for a single token_symbol.
    """
    pool = current_state['pool'].copy()
    tokens_in_symbol = input_params.token_in.symbol
    token_in_amount = input_params.token_in.amount
    pool_amount_out_expected = output_params.pool_amount_out
    swap_fee = pool['swap_fee']

    total_weight = calculate_total_denorm_weight(pool)

    join_swap = BalancerMath.calc_pool_out_given_single_in(
        token_balance_in=Decimal(pool['tokens'][tokens_in_symbol].balance),
        token_weight_in=Decimal(pool['tokens'][tokens_in_symbol].denorm_weight),
        pool_supply=Decimal(pool['pool_shares']),
        total_weight=total_weight,
        token_amount_in=token_in_amount,
        swap_fee=Decimal(swap_fee)
    )

    pool["generated_fees"] = update_fee(tokens_in_symbol, join_swap.fee, pool)

    pool_amount_out = join_swap.result
    if pool_amount_out != pool_amount_out_expected and VERBOSE:
        print(
            "WARNING: calculated that user should get {} pool shares but input specified that he should get {} pool shares instead.".format(
                pool_amount_out, pool_amount_out_expected))

    pool['pool_shares'] = Decimal(pool['pool_shares']) + pool_amount_out
    pool['tokens'][tokens_in_symbol].balance += token_in_amount

    return pool


def p_join_swap_pool_amount_out(params, step, history, current_state, input_params: JoinSwapPoolAmountOutInput,
                                output_params: JoinSwapPoolAmountOutOutput):
    pool = current_state['pool'].copy()
    max_token_in_amount = input_params.max_token_in.symbol
    tokens_in_symbol = input_params.max_token_in.symbol
    pool_amount_out = input_params.pool_amount_out
    swap_fee = pool['swap_fee']

    total_weight = calculate_total_denorm_weight(pool)

    join_swap = BalancerMath.calc_single_in_given_pool_out(
        token_balance_in=Decimal(pool['tokens'][tokens_in_symbol].balance),
        token_weight_in=Decimal(pool['tokens'][tokens_in_symbol].denorm_weight),
        pool_supply=Decimal(pool['pool_shares']),
        total_weight=total_weight,
        pool_amount_out=pool_amount_out,
        swap_fee=Decimal(swap_fee))

    pool["generated_fees"] = update_fee(tokens_in_symbol, join_swap.fee, pool)

    token_in_amount = join_swap.result
    if token_in_amount > max_token_in_amount and VERBOSE:
        print(
            "WARNING: calculated that user should get {} pool shares but input specified that he should get {} pool shares instead.".format(
                pool_amount_out, max_token_in_amount))

    pool['pool_shares'] = Decimal(pool['pool_shares']) + pool_amount_out
    pool['tokens'][tokens_in_symbol].balance += token_in_amount

    return pool


def p_exit_swap_extern_amount_out(params, step, history, current_state, input_params: ExitSwapPoolExternAmountOutInput,
                                  output_params: ExitSwapPoolExternAmountOutOutput) -> dict:
    """
    Exit a pool by withdrawing liquidity for a single token_symbol.
    """
    pool = current_state['pool'].copy()
    swap_fee = pool['swap_fee']
    token_out_symbol = input_params.token_out.symbol
    # Check that all tokens_out are bound
    if not pool['tokens'][token_out_symbol].bound:
        raise Exception("ERR_NOT_BOUND")
    # Check that user is not trying to withdraw too many tokens
    token_amount_out = input_params.token_out.amount
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

    pool["generated_fees"] = update_fee(token_out_symbol, exit_swap.fee, pool)

    if pool_amount_in == 0:
        raise Exception("ERR_MATH_APPROX")
    if pool_amount_in != output_params.pool_amount_in and VERBOSE:
        print(
            "WARNING: calculated that pool should get {} pool shares but input specified that pool should get {} pool shares instead".format(
                pool_amount_in, output_params.pool_amount_in))

    # Decrease token_symbol (give it to user)
    pool['tokens'][token_out_symbol].balance -= token_amount_out
    # Burn the user's incoming pool shares - exit fee
    exit_fee = pool_amount_in * EXIT_FEE
    pool['pool_shares'] = Decimal(pool['pool_shares']) - pool_amount_in - exit_fee

    return pool


def p_exit_swap_pool_amount_in(params, step, history, current_state, input_params: ExitSwapPoolAmountInInput,
                               output_params: ExitSwapPoolAmountInOutput) -> dict:
    pool = current_state['pool'].copy()
    swap_fee = pool['swap_fee']
    pool_token_out = pool['tokens'][output_params.token_out.symbol]
    if not pool_token_out.bound:
        raise Exception("ERR_NOT_BOUND")
    pool_amount_in = input_params.pool_amount_in
    total_weight = calculate_total_denorm_weight(pool)

    exit_swap = BalancerMath.calc_single_out_given_pool_in(
        token_balance_out=Decimal(pool_token_out.balance),
        token_weight_out=Decimal(pool_token_out.denorm_weight),
        pool_supply=Decimal(pool['pool_shares']),
        total_weight=Decimal(total_weight),
        pool_amount_in=pool_amount_in,
        swap_fee=Decimal(swap_fee))

    token_amount_out = exit_swap.result
    if token_amount_out > pool_token_out.balance * MAX_OUT_RATIO:
        raise Exception("ERR_MAX_OUT_RATIO")

    generated_fees = pool['generated_fees']
    generated_fees[output_params.token_out.symbol] = Decimal(generated_fees[output_params.token_out.symbol]) + exit_swap.fee

    pool['tokens'][output_params.token_out.symbol].balance -= token_amount_out

    # Burn the user's incoming pool shares - exit fee
    exit_fee = pool_amount_in * EXIT_FEE
    pool['pool_shares'] = Decimal(pool['pool_shares']) - pool_amount_in - exit_fee

    return pool


def p_exit_pool(params, step, history, current_state, input_params: ExitPoolInput, output_params: ExitPoolOutput) -> dict:
    """
    Exit a pool by withdrawing liquidity for all token_symbol.
    """
    pool = current_state['pool'].copy()
    pool_shares = Decimal(pool['pool_shares'])
    pool_amount_in = input_params.pool_amount_in

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


# PLOT OUTPUT

def p_join_pool_plot_output(params, step, history, current_state, input_params: JoinParamsInput, output_params: JoinParamsOutput) -> dict:
    pool = current_state['pool'].copy()
    pool_amount_out = input_params.pool_amount_out
    for token in output_params.tokens_in:
        pool['tokens'][token.symbol].balance += token.amount
    pool['pool_shares'] += pool_amount_out
    return pool


def p_join_swap_plot_output(params, step, history, current_state, input_params: JoinSwapExternAmountInInput,
                            output_params: JoinSwapExternAmountInOutput) -> dict:
    pool = current_state['pool'].copy()
    tokens_in_symbol = input_params.token_in.symbol
    pool['pool_shares'] = Decimal(pool['pool_shares']) + output_params.pool_amount_out
    pool['tokens'][tokens_in_symbol].balance += input_params.token_in.amount
    return pool


def p_exit_swap_plot_output(params, step, history, current_state, input_params, output_params):
    pool = current_state['pool'].copy()
    pool_token_out = pool['tokens'][output_params.token_out.symbol]
    if not pool_token_out.bound:
        raise Exception("ERR_NOT_BOUND")
    pool_amount_in = input_params.pool_amount_in

    pool['tokens'][output_params.token_out.symbol].balance -= output_params.token_out.amount

    # Burn the user's incoming pool shares - exit fee
    exit_fee = pool_amount_in * EXIT_FEE
    pool['pool_shares'] = Decimal(pool['pool_shares']) - pool_amount_in - exit_fee

    return pool


def p_exit_pool_plot_output(params, step, history, current_state, input_params, output_params):
    pool = current_state['pool'].copy()
    pool_shares = Decimal(pool['pool_shares'])
    pool_amount_in = input_params.pool_amount_in

    # Current Balancer implementation has 0 exit fees, but we are leaving this to generalize
    exit_fee = pool_amount_in * Decimal(EXIT_FEE)
    pool_amount_in_afer_exit_fee = pool_amount_in - exit_fee
    ratio = pool_amount_in_afer_exit_fee / pool_shares

    pool['pool_shares'] = pool_shares - pool_amount_in_afer_exit_fee

    for token in output_params.tokens_out:
        pool['tokens'][token.symbol].balance -= token.amount

    return pool
