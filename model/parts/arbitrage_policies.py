from pprint import pprint as pp
from datetime import timedelta
import pandas as pd
from decimal import Context, Decimal, MAX_EMAX
from operator import itemgetter, attrgetter
import typing
import dateutil
from attr import dataclass

from model.parts.balancer_constants import MAX_IN_RATIO
from model.parts.balancer_math import BalancerMath
from model.parts.pool_method_entities import SwapExactAmountInInput, SwapExactAmountInOutput, TokenAmount

MAX_DECIMAL = Context(Emax=MAX_EMAX, prec=1).create_decimal('9e' + str(MAX_EMAX))
VERBOSE = True


def print_if_verbose(text: any, *args):
    if VERBOSE:
        print(text, *args)

@dataclass
class PotentialArbTradeLite:
    token_in: str
    token_out: str

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

def in_external_currency(i: typing.Dict, external_token_prices: typing.Dict) -> typing.Dict:
    """
    Example input
    i: A in other tokens {'B': Decimal('1.0'), 'C': Decimal('1.2'), 'D': Decimal('3')}
    external_token_prices: {'A': Decimal('0.5'), 'B': Decimal('1'), 'C': Decimal('1'), 'D': Decimal('1')}
    """
    for k in i.keys():
        i[k] = (1 / i[k]) * external_token_prices[k]
    return i

def find_profitable_trade_route(spot_prices, external_currency, external_token_prices) -> typing.List[typing.Tuple]:
    """
    Input parameter examples:
    spot_prices: {'AAVE': {'SNX': Decimal('0.0785761'), 'SUSHI': Decimal('0.0372485'), 'YFI': Decimal('170.813')}, 'SNX': {'AAVE': Decimal('12.7903'), 'SUSHI': Decimal('0.475231'), 'YFI': Decimal('2179.31')}, 'SUSHI': {'AAVE': Decimal('26.9814'), 'SNX': Decimal('2.11479'), 'YFI': Decimal('4597.28')}, 'YFI': {'AAVE': Decimal('0.00588370'), 'SNX': Decimal('0.000461163'), 'SUSHI': Decimal('0.000218611')}}
    external_currency: 'USDT'
    external_token_prices: {'AAVE': Decimal('178.0310000000000059117155'), 'SNX': Decimal('13.455000000000000071054273576'), 'SUSHI': Decimal('6.458000000000000184741111297')}

    x is token_in! You go into the pool with this token (which is supposed to
    be cheaper on the external markets) and come out with this other token
    (which has more value)
    """
    x_spot_price_cheaper_than_external_price = []
    for x, x_spot_price_in_others in spot_prices.items():
        x_in_external_currency = external_token_prices[x]
        x_spot_price_in_others_in_external_currency = in_external_currency(x_spot_price_in_others, external_token_prices)
        print_if_verbose(f'1 {x} (token_in) is ~{x_in_external_currency:.2f} {external_currency} on external markets, can come out via {x_spot_price_in_others_in_external_currency} {external_currency} (token_out)')

        # if the pool has a cheap token (in external_currency) which can be sold outside for higher price, take note of it
        cheaper_than_external_price = [(PotentialArbTradeLite(token_in=x, token_out=token_out_symbol), x_in_external_currency / token_out_in_external_currency) for token_out_symbol, token_out_in_external_currency in x_spot_price_in_others_in_external_currency.items() if x_in_external_currency < token_out_in_external_currency]

        x_spot_price_cheaper_than_external_price.extend(cheaper_than_external_price)
    x_spot_price_cheaper_than_external_price = sorted(x_spot_price_cheaper_than_external_price, key=itemgetter(1))
    # print_if_verbose("tokens whose spot price is cheaper than external price", x_spot_price_cheaper_than_external_price)
    return x_spot_price_cheaper_than_external_price

def p_arbitrageur(params, substep, history, current_state):
    pool = current_state['pool']
    spot_prices = current_state['spot_prices']
    external_currency = params[0]['external_currency']
    potential_trades = []
    print_if_verbose('============================================')
    print_if_verbose("Timestep", current_state['timestep'], pool)
    external_token_prices = dict((k, Decimal(v)) for k, v in current_state['token_prices'].items())

    x_spot_price_cheaper_than_external_price = find_profitable_trade_route(spot_prices, external_currency, external_token_prices)

    print_if_verbose("calculating optimal trade size")
    if not len(x_spot_price_cheaper_than_external_price):
        print_if_verbose('no trade')
        return {'external_price_update': None, 'change_datetime_update': None, 'action_type': None,
            'pool_update': None}

    the_trade = x_spot_price_cheaper_than_external_price[0][0]
    calculate_optimal_trade_size(params, current_state, the_trade.token_in, the_trade.token_out, external_token_prices, potential_trades)
    potential_trades = sorted(potential_trades, key=attrgetter('profit'), reverse=True)
    if not len(potential_trades):
        print_if_verbose('no trade')
        return {'external_price_update': None, 'change_datetime_update': None, 'action_type': None,
            'pool_update': None}

    # Filter out profit < transaction cost; trades raising security exceptions in pool
    potential_trades = list(filter(lambda trade: trade.profit > trade.transaction_cost, potential_trades))
    potential_trades = list(filter(lambda trade: trade.token_amount_in < pool.tokens[trade.token_in].balance * MAX_IN_RATIO, potential_trades))
    # pp(potential_trades)
    most_profitable_trade = potential_trades[0]
    print_if_verbose(f'most_profitable_trade: {most_profitable_trade.token_amount_in:.3f} {most_profitable_trade.token_in} -> {most_profitable_trade.token_amount_out:.3f} {most_profitable_trade.token_out}, profit {most_profitable_trade.profit:.3f} {external_currency}')
    swap_input = SwapExactAmountInInput(token_in=TokenAmount(
        symbol=most_profitable_trade.token_in,
        amount=most_profitable_trade.token_amount_in
    ), min_token_out=TokenAmount(
        symbol=most_profitable_trade.token_out,
        amount=Decimal('0')
    ))

    swap_output = SwapExactAmountInOutput(token_out=TokenAmount(amount=most_profitable_trade.token_amount_out, symbol=most_profitable_trade.token_out))
    # print_if_verbose(swap_input, swap_output)
    # add 15 seconds, more or less next block
    action_datetime = current_state['change_datetime'] + timedelta(0, 15)
    return {
        'pool_update': (swap_input, swap_output),
        'change_datetime_update': pd.Timestamp(action_datetime.isoformat()),
        'action_type': 'swap',
    }

def p_arbitrageur0(params, substep, history, current_state):
    pool = current_state['pool']
    spot_prices = current_state['spot_prices']
    external_currency = params[0]['external_currency']
    potential_trades = []
    print_if_verbose('============================================')
    print_if_verbose("Timestep", current_state['timestep'], pool)
    external_token_prices = dict((k, Decimal(v)) for k, v in current_state['token_prices'].items())
    for token_in in spot_prices.keys():
        print_if_verbose('token_in', token_in)
        for token_out in spot_prices[token_in].keys():
            print_if_verbose('token_out', token_out)
            spot_price_token_in = spot_prices[token_out][token_in]
            print_if_verbose(f'spot price: 1 {token_in} = {spot_price_token_in} {token_out}', )
            print_if_verbose(f'external price token in: 1{token_in} = {external_token_prices[token_in]} {external_currency}')
            print_if_verbose(f'external price token out: 1{token_out} = {external_token_prices[token_out]} {external_currency}')
            spot_price_token_in_external_currency = spot_price_token_in * external_token_prices[token_out]
            import ipdb; ipdb.set_trace()
            print_if_verbose(f'spot_price_token_in external curr: 1 {token_in} = {spot_price_token_in_external_currency} {external_currency}')
            # sell token out in external market. Price outside must be bigger than spot price in
            print_if_verbose(f'{spot_price_token_in_external_currency} < {external_token_prices[token_in]}')
            if spot_price_token_in_external_currency < external_token_prices[token_in]:
                print_if_verbose('possible trade')
                calculate_optimal_trade_size(params, current_state, token_out, token_in, external_token_prices, potential_trades)
            else:
                print_if_verbose('no trade')
    # Sort by profitERR_MAX_IN_RATIO
    potential_trades = sorted(potential_trades, key=attrgetter('profit'), reverse=True)
    # Filter out profit < transaction cost
    potential_trades = list(filter(lambda trade: trade.profit > trade.transaction_cost, potential_trades))
    # Filter out trades raising security exceptions in pool
    potential_trades = list(filter(lambda trade: trade.token_amount_in < pool.tokens[trade.token_in].balance * MAX_IN_RATIO, potential_trades))

    if len(potential_trades) > 0:
        most_profitable_trade = potential_trades[0]
        print_if_verbose('most_profitable_trade', most_profitable_trade)
        swap_input = SwapExactAmountInInput(token_in=TokenAmount(
            symbol=most_profitable_trade.token_in,
            amount=most_profitable_trade.token_amount_in
        ), min_token_out=TokenAmount(
            symbol=most_profitable_trade.token_out,
            amount=Decimal('0')
        ))

        swap_output = SwapExactAmountInOutput(token_out=TokenAmount(amount=most_profitable_trade.token_amount_out, symbol=most_profitable_trade.token_out))
        print_if_verbose(swap_input, swap_output)
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
