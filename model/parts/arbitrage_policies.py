from datetime import timedelta
import pandas as pd
from decimal import Context, Decimal, MAX_EMAX
from operator import attrgetter

import dateutil
from attr import dataclass
from model.parts.balancer_math import BalancerMath
from model.parts.pool_method_entities import SwapExactAmountInInput, SwapExactAmountInOutput, TokenAmount

MAX_DECIMAL = Context(Emax=MAX_EMAX, prec=1).create_decimal('9e' + str(MAX_EMAX))
VERBOSE = True


def print_if_verbose(text: any, *args):
    if VERBOSE:
        print(text, *args)


@dataclass
class PotentialArbTrade:
    token_in: str
    token_amount_in: Decimal
    liquidity_in: Decimal
    token_out: str
    token_amount_out: Decimal
    transaction_cost: Decimal
    profit: Decimal


def calculate_optimal_trade_size(params, current_state, token_in, token_out, external_token_prices, potential_trades):
    max_arb_liquidity = params[0]['max_arb_liquidity']  # usd
    min_arb_liquidity = params[0]['min_arb_liquidity']  # usd
    arb_liquidity_granularity = params[0]['arb_liquidity_granularity']  # usd
    transaction_cost = current_state['gas_cost']
    pool = current_state['pool']
    pool_token_in = pool.tokens[token_in]
    pool_token_out = pool.tokens[token_out]
    for arb_liq in range(min_arb_liquidity, max_arb_liquidity, arb_liquidity_granularity):
        # 1000 usd
        # 1000 usd to amount_in using external price
        # a_o  = out_given_in
        # a_o_us = a_o converted to external price
        # profit = a_o_us - cost 
        # add to potential_trades
        # sort by biggest profit
        # select biggest profit && profit >= gas cost
        # print('Arb liq', arb_liq)
        token_amount_in = external_token_prices[token_in] * Decimal(arb_liq)
        # print('token_amount_in', token_amount_in)
        swap_result = BalancerMath.calc_out_given_in(
            token_balance_in=pool_token_in.balance,
            token_weight_in=Decimal(pool_token_in.denorm_weight),
            token_balance_out=pool_token_out.balance,
            token_weight_out=Decimal(pool_token_out.denorm_weight),
            token_amount_in=token_amount_in,
            swap_fee=pool.swap_fee
        )
        # print('token_amount_out', swap_result.result)
        amount_out_external_price = external_token_prices[token_out] * swap_result.result
        # print('amount_out_external_price', amount_out_external_price)
        profit = amount_out_external_price - transaction_cost
        # print('profit', profit)
        potential_trades.append(PotentialArbTrade(
            token_in=token_in,
            token_amount_in=token_amount_in,
            liquidity_in=Decimal(arb_liq),
            token_out=token_out,
            token_amount_out=swap_result.result,
            transaction_cost=transaction_cost,
            profit=profit
        ))


def p_arbitrageur(params, step, history, current_state):
    pool = current_state['pool']
    spot_prices = current_state['spot_prices']
    external_currency = params[0]['external_currency']
    potential_trades = []
    # token out : token_in
    external_token_prices = dict((k, Decimal(v)) for k, v in current_state['token_prices'].items())
    for token_out in spot_prices.keys():
        print_if_verbose('token_out', token_out)
        for token_in in spot_prices[token_out].keys():
            print_if_verbose('token_in', token_in)
            spot_price_token_in = spot_prices[token_out][token_in]
            print_if_verbose(f'spot price: 1 {token_in} = {spot_price_token_in} {token_out}', )
            print_if_verbose(f'external price token in: 1{token_in} = {external_token_prices[token_in]} {external_currency}')
            print_if_verbose(f'external price token out: 1{token_out} = {external_token_prices[token_out]} {external_currency}')
            spot_price_token_in_external_currency = spot_price_token_in * external_token_prices[token_out]
            print_if_verbose(f'spot_price_token_in external curr: 1 {token_in} = {spot_price_token_in_external_currency} {external_currency}')
            # sell token out in external market. Price outside must be bigger than spot price in
            print_if_verbose(f'{spot_price_token_in_external_currency} < {external_token_prices[token_in]}')
            if spot_price_token_in_external_currency < external_token_prices[token_in]:
                print_if_verbose('possible trade')
                calculate_optimal_trade_size(params, current_state, token_in, token_out, external_token_prices, potential_trades)

    # Sort by profit
    potential_trades = sorted(potential_trades, key=attrgetter('profit'), reverse=True)
    # Filter out profit < transaction cost
    potential_trades = list(filter(lambda trade: trade.profit > trade.transaction_cost, potential_trades))
    most_profitable_trade = potential_trades[0]
    print_if_verbose('most_profitable_trade', most_profitable_trade)
    if most_profitable_trade:
        swap_input = SwapExactAmountInInput(token_in=TokenAmount(
            symbol=most_profitable_trade.token_in,
            amount=most_profitable_trade.token_amount_in
        ), min_token_out=TokenAmount(
            symbol=most_profitable_trade.token_out,
            amount=Decimal('0')
        ))

        swap_output = SwapExactAmountInOutput(token_out=TokenAmount(amount=most_profitable_trade.token_amount_out, symbol=most_profitable_trade.token_out))
        print(swap_input, swap_output)
        # add 15 seconds, more or less next block
        action_datetime = current_state['change_datetime'] + timedelta(0, 15)
        return {
            'pool_update': (swap_input, swap_output),
            'change_datetime_update': pd.Timestamp(action_datetime.isoformat()),
            'action_type': 'swap',
        }
    print_if_verbose('no trade')
    return {'external_price_update': None, 'change_datetime_update': None, 'action_type': None,
            'pool_update': None}
