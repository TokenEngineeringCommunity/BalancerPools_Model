"""
Test harness to help pinpoint and develop p_arbitrageur() without having to run
the entire simulation.
"""
import unittest
import attr
from datetime import datetime
from decimal import Decimal
from model.models import Pool, Token
from model.parts.pool_method_entities import *
from model.parts.arbitrage_policies import *

class TestArbitrageAgent(unittest.TestCase):
    def setUp(self):
        self.params = {
            'external_currency': 'USD',
            'max_arb_liquidity': 100000,
            'min_arb_liquidity': 10,
            'arb_liquidity_granularity': 50,
        }


        self.current_state_template = {
            'timestep': 0,
            'gas_cost': Decimal(30),
            'change_datetime': datetime.fromisoformat('2020-12-07T13:34:14+00:00')
        }

    def test_assy(self):
        """
        In this situation, the arb agent shouldn't do anything, because
        everything is negative profit.
        """
        self.params['external_currency'] = 'USDT'
        pool = Pool(
            tokens={
                'AAVE': Token(denorm_weight=12, balance=Decimal(1000), bound=True),
                'SNX': Token(denorm_weight=10, balance=Decimal(11024), bound=True),
                'SUSHI': Token(denorm_weight=6, balance=Decimal(13781), bound=True),
                'YFI': Token(denorm_weight=12, balance=Decimal(5.969), bound=True),
            },
            generated_fees={},
            shares=Decimal(100),
            swap_fee=Decimal(0.0025)
        )
        """
        How to read spot_prices
        1 SNX = 0.0785 AAVE; 1 SUSHI = 0.0372 AAVE...
        """
        spot_prices = {
            'AAVE': {'SNX': Decimal('0.07857617457237274274633254625'), 'SUSHI': Decimal('0.03724850507780933347160619595'), 'YFI': Decimal('170.8138125173215948020742080')},
            'SNX': {'AAVE': Decimal('12.79037593984962406081767716'), 'SUSHI': Decimal('0.4752313271847226001641404904'), 'YFI': Decimal('2179.310945620995835122783575')},
            'SUSHI': {'AAVE': Decimal('26.98145363408521303398913369'), 'SNX': Decimal('2.114799162440839998274794150'), 'YFI': Decimal('4597.282950091193402503025234')},
            'YFI': {'AAVE': Decimal('0.005883709273182957165847140669'), 'SNX': Decimal('0.0004611635685652556093120720991'), 'SUSHI': Decimal('0.0002186114763016629696755272597')}
        }
        token_prices = {'AAVE': 178.031, 'SNX': 13.455, 'SUSHI': 6.458, 'YFI': 29822.5}

        current_state = self.current_state_template
        current_state['pool'] = pool
        current_state['spot_prices'] = spot_prices
        current_state['token_prices'] = token_prices

        answer = p_arbitrageur([self.params], 0, [], current_state)
        self.assertIsNone(answer['pool_update'])

    def test_wethdai(self):
        """
        The arb agent should decide to extract WETH from the pool, since the
        pool should quote a price of 591.985 DAI ->
        594.2136763859792659213742049 USD, which is less than the actual
        (external) price of 596.1937868299183 USD

        The exact size of the trade is important of course but this is tested in
        other unit tests. In this test we simply check that the arb agent
        decided to get WETH out of the pool.
        """
        pool = Pool(
            tokens={
                'DAI': Token(denorm_weight=10, balance=Decimal(10000000), bound=True),
                'WETH': Token(denorm_weight=40, balance=Decimal(67738.636173102396002749), bound=True),
            },
            generated_fees={},
            shares=Decimal(100),
            swap_fee=Decimal(0.0025)
        )
        spot_prices = {
            'WETH': {'DAI': Decimal('0.001697710179777002343786452713')},
            'DAI': {'WETH': Decimal('591.9849127769920066974429390')}
        }
        token_prices_in_usd = {'WETH': Decimal('596.1937868299183'), 'DAI': Decimal('1.0037648993426744')}

        current_state = self.current_state_template
        current_state['pool'] = pool
        current_state['spot_prices'] = spot_prices
        current_state['token_prices'] = token_prices_in_usd

        answer = p_arbitrageur([self.params], 0, [], current_state)

        self.assertEqual(answer['pool_update'][0].token_in.symbol, 'DAI')
        self.assertEqual(answer['pool_update'][1].token_out.symbol, 'WETH')

    def test_calculate_optimal_trade_size(self):
        pool = Pool(
            tokens={
                'DAI': Token(denorm_weight=10, balance=Decimal(10000000), bound=True),
                'WETH': Token(denorm_weight=40, balance=Decimal(67738.636173102396002749), bound=True),
            },
            generated_fees={},
            shares=Decimal(100),
            swap_fee=Decimal(0.0025)
        )
        token_prices_in_usd = {'WETH': Decimal('596.1937868299183'), 'DAI': Decimal('1.0037648993426744')}
        e = ExternalPrices(symbol='USD', external_prices=token_prices_in_usd)

        arb_iterations = calculate_optimal_trade_size(pool, 1000, 10000, 1000, self.current_state_template['gas_cost'], 'WETH', 'DAI', e)

    def test_calculate_profit_1000usd_outweth(self):
        liquidity_in = TokenAmount(symbol='USD', amount=Decimal(1000))
        token_in = TokenAmount(symbol='DAI', amount=Decimal('996.2492219591062783464561372'))
        token_out = TokenAmount(symbol='WETH', amount=Decimal('1.682791787624291356513366976'))
        tx_cost_in_external_currency = TokenAmount(symbol='USD', amount=Decimal(30))

        token_prices_in_usd = {'WETH': Decimal('596.1937868299183'), 'DAI': Decimal('1.0037648993426744')}
        e = ExternalPrices(symbol='USD', external_prices=token_prices_in_usd)

        j = calculate_profit(liquidity_in, token_in, token_out, tx_cost_in_external_currency, e)

        j_expected = {'liquidity_in': {'symbol': 'USD', 'amount': Decimal('1000')}, 'token_in': {'symbol': 'DAI', 'amount': Decimal('996.2492219591062783464561372')}, 'token_out': {'symbol': 'WETH', 'amount': Decimal('1.682791787624291356513366976')}, 'effective_token_out_price_in_external_currency': {'symbol': 'USD', 'amount': Decimal('594.2505824869553500800156732')}, 'effective_token_out_price_gap_to_external_price': {'symbol': 'USD', 'amount': Decimal('1.9432043429629499199843268')}, 'tx_cost_in_external_currency': {'symbol': 'USD', 'amount': Decimal('30')}, 'profit': {'symbol': 'USD', 'amount': Decimal('-26.72999168998609095410706169')}}

        self.assertEqual(attr.asdict(j), j_expected)

    def test_calculate_profit_1000usd_outdai(self):
        liquidity_in = TokenAmount(symbol='USD', amount=Decimal(1000))
        token_in = TokenAmount(symbol='WETH', amount=Decimal('1.677306979861699267518102426'))
        token_out = TokenAmount(symbol='DAI', amount=Decimal('987.9209261656465683173860000'))
        tx_cost_in_external_currency = TokenAmount(symbol='USD', amount=Decimal(30))

        token_prices_in_usd = {'WETH': Decimal('596.1937868299183'), 'DAI': Decimal('1.0037648993426744')}
        e = ExternalPrices(symbol='USD', external_prices=token_prices_in_usd)

        j = calculate_profit(liquidity_in, token_in, token_out, tx_cost_in_external_currency, e)
        j_expected = {'liquidity_in': {'symbol': 'USD', 'amount': Decimal('1000')}, 'token_in': {'symbol': 'WETH', 'amount': Decimal('1.677306979861699267518102426')}, 'token_out': {'symbol': 'DAI', 'amount': Decimal('987.9209261656465683173860000')}, 'effective_token_out_price_in_external_currency': {'symbol': 'USD', 'amount': Decimal('1.012226761792803759832496885')}, 'effective_token_out_price_gap_to_external_price': {'symbol': 'USD', 'amount': Decimal('-0.008461862450129359832496885')}, 'tx_cost_in_external_currency': {'symbol': 'USD', 'amount': Decimal('30')}, 'profit': {'symbol': 'USD', 'amount': Decimal('-38.35965098881810446194520381')}}

        self.assertEqual(attr.asdict(j), j_expected)
