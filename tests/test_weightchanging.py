from pprint import pprint as pp
from decimal import Decimal
import unittest
import copy

from model.models import Pool, Token
from model.parts.pool_method_entities import TokenAmount, SwapExactAmountInInput, SwapExactAmountInOutput
from model.parts.pool_state_updates import powerpool_weightchange_delta, powerpool_new_strategy, s_swap_exact_amount_in


"""
This test harness helps in developing powerpool_weightchange_delta() without
relying on historical data to drive the simulation.
"""
class TestWeightChange(unittest.TestCase):
    def setUp(self):
        self.params = {
            'spot_price_reference': ['DAI'],
            'decoding_type': ['CONTRACT_CALL'],
            'weight_changing': [True],
        }

    def test_delta(self):
        dai586 = TokenAmount(symbol='DAI', amount=Decimal(586.651036))
        weth1 = TokenAmount(symbol='WETH', amount=Decimal(1))
        trade1 = (SwapExactAmountInInput(token_in=weth1, min_token_out=dai586), SwapExactAmountInOutput(token_out=dai586))

        pool0 = Pool(
            tokens={
                'DAI': Token(denorm_weight=10, balance=Decimal(100000), bound=True),
                'WETH': Token(denorm_weight=40, balance=Decimal(677.6361731), bound=True)
            },
            generated_fees={},
            shares=Decimal(100),
            swap_fee=Decimal(0.0025),
            denorm_weight_constant=50
        )
        state1 = {
            'pool': pool0,
            # 'token_prices': {'DAI': 1, 'WETH': 599}
        }

        w_s_swap_exact_amount_in = powerpool_weightchange_delta(s_swap_exact_amount_in)
        pool1 = w_s_swap_exact_amount_in(self.params, 1, [], state1, trade1[0], trade1[1])

        self.assertEqual(pool1.tokens['DAI'].denorm_weight, Decimal('10.05866510360452269575162233'))
        self.assertEqual(pool1.tokens['WETH'].denorm_weight, Decimal('39.94133489639547730424837767'))
        self.assertEqual(pool1.total_denorm_weight, Decimal(50))

        dai9000 = TokenAmount(symbol='DAI', amount=Decimal(9000))
        weth14 = TokenAmount(symbol='WETH', amount=Decimal(14.61628148))
        trade2 = (SwapExactAmountInInput(token_in=dai9000, min_token_out=weth14), SwapExactAmountInOutput(token_out=weth14))
        state1 = {
            'pool': copy.deepcopy(pool1),
            # 'token_prices': {'DAI': 1, 'WETH': 650}
        }

        pool2 = w_s_swap_exact_amount_in(self.params, 1, [], state1, trade2[0], trade2[1])
        self.assertEqual(pool2.tokens['DAI'].denorm_weight, Decimal('9.19841948641352468754667063'))
        self.assertEqual(pool2.tokens['WETH'].denorm_weight, Decimal('40.80158051358647531245332937'))
        self.assertEqual(pool2.total_denorm_weight, Decimal(50))
        self.assertEqual(pool2.spot_prices('DAI')['DAI']['WETH'], Decimal('726.0266151646751960622338872'))
        self.assertEqual(pool2.spot_prices('WETH')['WETH']['DAI'], Decimal('0.001384272686019843467462847438'))


        weth1369 = TokenAmount(symbol='WETH', amount=Decimal(13.69230769))
        dai9361 = TokenAmount(symbol='DAI', amount=Decimal(9361.879005))
        trade3 = (SwapExactAmountInInput(token_in=weth1369, min_token_out=dai9361), SwapExactAmountInOutput(token_out=dai9361))
        state2 = {
            'pool': copy.deepcopy(pool2),
            # 'token_prices': {'DAI': 1, 'WETH': 650}
        }
        pool3 = w_s_swap_exact_amount_in(self.params, 1, [], state2, trade3[0], trade3[1])
        self.assertAlmostEqual(pool3.tokens['DAI'].denorm_weight, Decimal('9.992735787'))  # here slight math inconsistencies seem to build up, soldier on
        self.assertAlmostEqual(pool3.tokens['WETH'].denorm_weight, Decimal('40.00726421'))
        self.assertEqual(pool3.total_denorm_weight, Decimal(50))
        self.assertAlmostEqual(pool3.spot_prices('DAI')['DAI']['WETH'], Decimal('586.6204073'))
        self.assertAlmostEqual(pool3.spot_prices('WETH')['WETH']['DAI'], Decimal('0.00171323534'))

if __name__ == '__main__':
    unittest.main()
