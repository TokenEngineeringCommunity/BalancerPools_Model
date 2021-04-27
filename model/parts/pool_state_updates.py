import ipdb
import copy
from decimal import Decimal

from model.parts.balancer_constants import (EXIT_FEE, MAX_IN_RATIO,
                                            MAX_OUT_RATIO)
from model.parts.balancer_math import BalancerMath
from model.parts.pool_method_entities import (
    ExitPoolInput, ExitPoolOutput, ExitSwapPoolAmountInInput,
    ExitSwapPoolAmountInOutput, ExitSwapPoolExternAmountOutInput,
    ExitSwapPoolExternAmountOutOutput, JoinParamsInput, JoinParamsOutput,
    JoinSwapExternAmountInInput, JoinSwapExternAmountInOutput,
    JoinSwapPoolAmountOutInput, JoinSwapPoolAmountOutOutput,
    PoolMethodParamsDecoder, SwapExactAmountInInput, SwapExactAmountInOutput,
    SwapExactAmountOutInput, SwapExactAmountOutOutput)
from model.parts.system_policies import ActionDecodingType
from model.parts.utils import get_param

VERBOSE = False


def s_update_pool(params, substep, state_history, previous_state, policy_input):
    pool_opcodes = policy_input.get('pool_update')
    # Here the contents of pool_opcodes should be e.g. (SwapExactAmountInInput, SwapExactAmountInOutput)
    if pool_opcodes is None:
        # This means there is no change to the pool. Return the pool but with 0 generated fees.
        return s_pool_update_fee(previous_state['pool'], {})

    decoding_type = get_param(params, "decoding_type")
    weight_change_factor = get_param(params, "weight_change_factor")
    if decoding_type == ActionDecodingType.replay_output:
        pool_operation_suf = pool_replay_output_mappings[type(pool_opcodes[0])]
    else:
        pool_operation_suf = pool_operation_mappings[type(pool_opcodes[0])]
        # TODO: make weight chaning on/off by parameter
        # pool_operation_suf = powerpool_linear_weight_change(pool_operation_suf, weight_change_factor)

    pool = pool_operation_suf(params, substep, state_history, previous_state, pool_opcodes[0], pool_opcodes[1])
    return 'pool', pool


def powerpool_linear_weight_change(state_update_function, weight_change_factor):
    def wrapped_state_update_function(*args, **kwargs):
        pool_opcode_in = args[4]
        pool_opcode_out = args[5]
        pool = state_update_function(*args, **kwargs)
        if type(pool_opcode_in) is SwapExactAmountInInput and type(pool_opcode_out) is SwapExactAmountInOutput:
            print("swap: will change weight")
            token_in = pool_opcode_in.token_in
            token_out = pool_opcode_out.token_out

            swap_size_proportion = token_in.amount / pool.tokens[token_in.symbol].balance
            print(token_in, "has a size of", swap_size_proportion)
            if swap_size_proportion > 1:
                raise Exception("WEIGHT CHANGE ERROR: swap amount being way larger than pool balance messes up the weight changing strategy")

            weight_increase_factor = Decimal(1) + Decimal(swap_size_proportion)
            weight_decrease_factor = Decimal(1) - Decimal(swap_size_proportion)
            pool_token_in = pool.tokens[token_in.symbol]
            print("Multiplying {}.denorm_weight by {}".format(token_in.symbol, weight_decrease_factor))
            pool_token_in_new_denorm_weight = pool_token_in.denorm_weight * weight_decrease_factor
            pool.change_weight(token_in.symbol, pool_token_in_new_denorm_weight)

            pool_token_out = pool.tokens[token_out.symbol]
            print("Multiplying {}.denorm_weight by {}".format(token_out.symbol, weight_increase_factor))
            pool_token_out_new_denorm_weight = pool_token_out.denorm_weight * weight_increase_factor
            pool.change_weight(token_out.symbol, pool_token_out_new_denorm_weight)

        elif type(pool_opcode_in) is SwapExactAmountOutInput:
            pass
        elif type(pool_opcode_in) in [JoinSwapExternAmountInInput, JoinSwapPoolAmountOutInput]:
            print("joinswap: won't change weight for now")
        elif type(pool_opcode_in) in [ExitSwapPoolExternAmountOutInput]:
            print("exitswap: won't change weight for now")
        return pool
    return wrapped_state_update_function


def s_update_spot_prices(params, substep, state_history, previous_state, policy_input):
    pool = previous_state["pool"]

    if isinstance(params, list):
        # 1 param or none
        ref_token = params[0].get('spot_price_reference')
    else:
        # Parameter sweep
        ref_token = params.get('spot_price_reference')

    spot_prices = pool.spot_prices(ref_token)
    return 'spot_prices', spot_prices


def s_pool_update_fee(pool, fees_per_token=dict()):
    for token in pool.generated_fees:
        pool.generated_fees[token] = fees_per_token.get(token, Decimal('0'))
    return "pool", pool


def s_swap_exact_amount_in(params, step, history, current_state, input_params: SwapExactAmountInInput,
                           output_params: SwapExactAmountInOutput) -> dict:
    pool = current_state['pool']
    # Parse action params
    token_in_symbol = input_params.token_in.symbol
    token_amount_in = input_params.token_in.amount
    token_out = input_params.min_token_out.symbol
    pool_token_in = pool.tokens[token_in_symbol]
    swap_fee = pool.swap_fee

    if not pool_token_in.bound:
        raise Exception('ERR_NOT_BOUND')
    out_record = pool.tokens[token_out]
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
        swap_fee=swap_fee
    )

    _, pool = s_pool_update_fee(pool, {token_in_symbol: swap_result.fee})
    pool_in_balance = pool_token_in.balance + token_amount_in
    pool_token_in.balance = pool_in_balance
    pool_out_balance = out_record.balance - swap_result.result
    out_record.balance = pool_out_balance
    return pool


def s_swap_exact_amount_out(params, step, history, current_state, input_params: SwapExactAmountOutInput,
                            output_params: SwapExactAmountOutOutput) -> dict:
    pool = current_state['pool']
    # Parse action params
    token_in_symbol = input_params.max_token_in.symbol
    token_amount_out = input_params.token_out.amount
    token_out_symbol = input_params.token_out.symbol
    pool_token_out = pool.tokens[token_out_symbol]
    pool_token_in = pool.tokens[token_in_symbol]
    swap_fee = pool.swap_fee

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

    _, pool = s_pool_update_fee(pool, {token_in_symbol: swap_result.fee})

    pool_token_in.balance = pool_token_in.balance + token_amount_in
    pool_token_out.balance = pool_token_out.balance - token_amount_out

    return pool


def s_join_pool(params, step, history, current_state, input_params: JoinParamsInput, output_params: JoinParamsOutput) -> dict:
    """
    Join a pool by providing liquidity for all token_symbols.
    """
    pool = current_state['pool']

    # tokens_in is a suggestion. The real fixed input is pool_amount_out - how many pool shares does the user want.
    # tokens_in will then be recalculated and that value used instead.
    pool_amount_out = input_params.pool_amount_out

    ratio = pool_amount_out / pool.shares
    if ratio == Decimal('0'):
        raise Exception("ERR_MATH_APPROX")

    for token in output_params.tokens_in:
        amount_expected = token.amount
        symbol = token.symbol
        amount = ratio * pool.tokens[symbol].balance
        if amount != amount_expected and VERBOSE:
            print("WARNING: calculated that user should get {} {} but input specified that he should get {} {} instead".format(amount, symbol,
                                                                                                                               amount_expected,
                                                                                                                               symbol))
        pool.tokens[symbol].balance += amount
    pool.shares += pool_amount_out

    return pool


def s_join_swap_extern_amount_in(params, step, history, current_state, input_params: JoinSwapExternAmountInInput,
                                 output_params: JoinSwapExternAmountInOutput) -> dict:
    """
    Join a pool by providing liquidity for a single token_symbol.
    """
    pool = current_state['pool']
    tokens_in_symbol = input_params.token_in.symbol
    token_in_amount = input_params.token_in.amount
    pool_amount_out_expected = output_params.pool_amount_out

    total_weight = pool.total_denorm_weight

    join_swap = BalancerMath.calc_pool_out_given_single_in(
        token_balance_in=Decimal(pool.tokens[tokens_in_symbol].balance),
        token_weight_in=Decimal(pool.tokens[tokens_in_symbol].denorm_weight),
        pool_supply=pool.shares,
        total_weight=total_weight,
        token_amount_in=token_in_amount,
        swap_fee=pool.swap_fee
    )

    _, pool = s_pool_update_fee(pool, {tokens_in_symbol: join_swap.fee})

    pool_amount_out = join_swap.result
    if pool_amount_out != pool_amount_out_expected and VERBOSE:
        print(
            "WARNING: calculated that user should get {} pool shares but input specified that he should get {} pool shares instead.".format(
                pool_amount_out, pool_amount_out_expected))

    pool.shares = pool.shares + pool_amount_out
    pool.tokens[tokens_in_symbol].balance += token_in_amount

    return pool


def s_join_swap_pool_amount_out(params, step, history, current_state, input_params: JoinSwapPoolAmountOutInput,
                                output_params: JoinSwapPoolAmountOutOutput):
    pool = current_state['pool']
    max_token_in_amount = input_params.max_token_in.symbol
    tokens_in_symbol = input_params.max_token_in.symbol
    pool_amount_out = input_params.pool_amount_out

    total_weight = pool.total_denorm_weight

    join_swap = BalancerMath.calc_single_in_given_pool_out(
        token_balance_in=Decimal(pool.tokens[tokens_in_symbol].balance),
        token_weight_in=Decimal(pool.tokens[tokens_in_symbol].denorm_weight),
        pool_supply=pool.shares,
        total_weight=total_weight,
        pool_amount_out=pool_amount_out,
        swap_fee=pool.swap_fee
    )

    _, pool = s_pool_update_fee(pool, {tokens_in_symbol: join_swap.fee})

    token_in_amount = join_swap.result
    if token_in_amount > max_token_in_amount and VERBOSE:
        print(
            "WARNING: calculated that user should get {} pool shares but input specified that he should get {} pool shares instead.".format(
                pool_amount_out, max_token_in_amount))

    pool.shares += pool.shares + pool_amount_out
    pool.tokens[tokens_in_symbol].balance += token_in_amount

    return pool


def s_exit_swap_extern_amount_out(params, step, history, current_state, input_params: ExitSwapPoolExternAmountOutInput,
                                  output_params: ExitSwapPoolExternAmountOutOutput) -> dict:
    """
    Exit a pool by withdrawing liquidity for a single token_symbol.
    """
    pool = current_state['pool']
    token_out_symbol = input_params.token_out.symbol
    # Check that all tokens_out are bound
    if not pool.tokens[token_out_symbol].bound:
        raise Exception("ERR_NOT_BOUND")
    # Check that user is not trying to withdraw too many tokens
    token_amount_out = input_params.token_out.amount
    if token_amount_out > Decimal(pool.tokens[token_out_symbol].balance) * MAX_OUT_RATIO:
        raise Exception("ERR_MAX_OUT_RATIO")

    total_weight = pool.total_denorm_weight

    exit_swap = BalancerMath.calc_pool_in_given_single_out(
        token_balance_out=Decimal(pool.tokens[token_out_symbol].balance),
        token_weight_out=Decimal(pool.tokens[token_out_symbol].denorm_weight),
        pool_supply=pool.shares,
        total_weight=Decimal(total_weight),
        token_amount_out=token_amount_out,
        swap_fee=pool.swap_fee
    )
    pool_amount_in = exit_swap.result

    _, pool = s_pool_update_fee(pool, {token_out_symbol: exit_swap.fee})

    if pool_amount_in == 0:
        raise Exception("ERR_MATH_APPROX")
    if pool_amount_in != output_params.pool_amount_in and VERBOSE:
        print(
            "WARNING: calculated that pool should get {} pool shares but input specified that pool should get {} pool shares instead".format(
                pool_amount_in, output_params.pool_amount_in))

    # Decrease token_symbol (give it to user)
    pool.tokens[token_out_symbol].balance -= token_amount_out
    # Burn the user's incoming pool shares - exit fee
    exit_fee = pool_amount_in * EXIT_FEE
    pool.shares = pool.shares - pool_amount_in - exit_fee

    return pool


def s_exit_swap_pool_amount_in(params, step, history, current_state, input_params: ExitSwapPoolAmountInInput,
                               output_params: ExitSwapPoolAmountInOutput) -> dict:
    pool = current_state['pool']
    swap_fee = pool.swap_fee
    pool_token_out = pool.tokens[output_params.token_out.symbol]
    if not pool_token_out.bound:
        raise Exception("ERR_NOT_BOUND")
    pool_amount_in = input_params.pool_amount_in
    total_weight = pool.total_denorm_weight

    exit_swap = BalancerMath.calc_single_out_given_pool_in(
        token_balance_out=Decimal(pool_token_out.balance),
        token_weight_out=Decimal(pool_token_out.denorm_weight),
        pool_supply=pool.shares,
        total_weight=Decimal(total_weight),
        pool_amount_in=pool_amount_in,
        swap_fee=Decimal(swap_fee))

    token_amount_out = exit_swap.result
    if token_amount_out > pool_token_out.balance * MAX_OUT_RATIO:
        raise Exception("ERR_MAX_OUT_RATIO")

    generated_fees = pool.generated_fees
    generated_fees[output_params.token_out.symbol] = Decimal(generated_fees[output_params.token_out.symbol]) + exit_swap.fee

    pool.tokens[output_params.token_out.symbol].balance -= token_amount_out

    # Burn the user's incoming pool shares - exit fee
    exit_fee = pool_amount_in * EXIT_FEE
    pool.shares = pool.shares - pool_amount_in - exit_fee

    return pool


def s_exit_pool(params, step, history, current_state, input_params: ExitPoolInput, output_params: ExitPoolOutput) -> dict:
    """
    Exit a pool by withdrawing liquidity for all token_symbol.
    """
    pool = current_state['pool']
    pool_amount_in = input_params.pool_amount_in

    # Current Balancer implementation has 0 exit fees, but we are leaving this to generalize
    exit_fee = pool_amount_in * Decimal(EXIT_FEE)
    pool_amount_in_after_exit_fee = pool_amount_in - exit_fee
    ratio = pool_amount_in_after_exit_fee / pool.shares

    pool.shares -= pool_amount_in_after_exit_fee

    for token_symbol in pool.tokens:
        token_amount_out = ratio * pool.tokens[token_symbol].balance
        if token_amount_out == Decimal('0'):
            raise Exception("ERR_MATH_APPROX")
        pool.tokens[token_symbol].balance -= token_amount_out

    return pool


# PLOT OUTPUT

def s_join_pool_plot_output(params, step, history, current_state, input_params: JoinParamsInput, output_params: JoinParamsOutput) -> dict:
    pool = current_state['pool']
    pool_amount_out = input_params.pool_amount_out
    for token in output_params.tokens_in:
        pool.tokens[token.symbol].balance += token.amount
    pool.shares += pool_amount_out
    return pool


def s_swap_plot_output(params, step, history, current_state, input_params: SwapExactAmountInInput,
                       output_params: SwapExactAmountInOutput) -> dict:
    pool = current_state['pool']
    pool_token_in = pool.tokens[input_params.token_in.symbol]
    pool_token_out = pool.tokens[output_params.token_out.symbol]

    pool_token_in.balance = pool_token_in.balance + input_params.token_in.amount
    pool_token_out.balance = pool_token_out.balance - output_params.token_out.amount
    return pool


def s_join_swap_plot_output(params, step, history, current_state, input_params: JoinSwapExternAmountInInput,
                            output_params: JoinSwapExternAmountInOutput) -> dict:
    pool = current_state['pool']
    tokens_in_symbol = input_params.token_in.symbol
    pool.shares = pool.shares + output_params.pool_amount_out
    pool.tokens[tokens_in_symbol].balance += input_params.token_in.amount
    return pool


def s_exit_swap_plot_output(params, step, history, current_state, input_params, output_params):
    pool = current_state['pool']
    pool_token_out = pool.tokens[output_params.token_out.symbol]
    if not pool_token_out.bound:
        raise Exception("ERR_NOT_BOUND")
    pool_amount_in = input_params.pool_amount_in

    pool.tokens[output_params.token_out.symbol].balance -= output_params.token_out.amount

    # Burn the user's incoming pool shares - exit fee
    exit_fee = pool_amount_in * EXIT_FEE
    pool.shares = pool.shares - pool_amount_in - exit_fee

    return pool


def s_exit_pool_plot_output(params, step, history, current_state, input_params, output_params):
    pool = current_state['pool']
    pool_shares = pool.shares
    pool_amount_in = input_params.pool_amount_in

    # Current Balancer implementation has 0 exit fees, but we are leaving this to generalize
    exit_fee = pool_amount_in * Decimal(EXIT_FEE)
    pool_amount_in_after_exit_fee = pool_amount_in - exit_fee
    ratio = pool_amount_in_after_exit_fee / pool_shares

    pool.shares = pool_shares - pool_amount_in_after_exit_fee

    for token in output_params.tokens_out:
        pool.tokens[token.symbol].balance -= token.amount

    return pool


pool_operation_mappings = {
    JoinSwapExternAmountInInput: s_join_swap_extern_amount_in,
    JoinParamsInput: s_join_pool,
    SwapExactAmountInInput: s_swap_exact_amount_in,
    SwapExactAmountOutInput: s_swap_exact_amount_out,
    ExitPoolInput: s_exit_pool,
    ExitSwapPoolAmountInInput: s_exit_swap_pool_amount_in,
    ExitSwapPoolExternAmountOutInput: s_exit_swap_extern_amount_out
}

pool_replay_output_mappings = {
    JoinSwapExternAmountInInput: s_join_swap_plot_output,
    JoinParamsInput: s_join_pool_plot_output,
    SwapExactAmountInInput: s_swap_plot_output,
    ExitPoolInput: s_exit_pool_plot_output,
    ExitSwapPoolAmountInInput: s_exit_swap_plot_output,
}
