from pprint import pprint as pp
from decimal import Decimal
import unittest

from model.models import Pool, Token
from model.parts.pool_method_entities import *
from model.parts.pool_state_updates import *


"""
This test harness helps in developing powerpool_linear_weight_change() without
relying on historical data to drive the simulation.
"""
class TestWeightChange(unittest.TestCase):
    def setUp(self):
        self.params = {
            'spot_price_reference': ['DAI'],
            'decoding_type': ['CONTRACT_CALL'],
            'weight_changing': [True],
        }

        dai10 = TokenAmount(symbol='DAI', amount=Decimal(100))
        weth10 = TokenAmount(symbol='WETH', amount=Decimal(10))
        self.opcodes = (SwapExactAmountInInput(token_in=dai10, min_token_out=weth10), SwapExactAmountInOutput(token_out=weth10))

        self.pool = Pool(
            tokens={
                'DAI': Token(denorm_weight=20, balance=Decimal(1000), bound=True),
                'WETH': Token(denorm_weight=20, balance=Decimal(1000), bound=True)
            },
            generated_fees={},
            shares=Decimal(100),
            swap_fee=Decimal(0.0025)
        )
        self.state_current = {
            'pool': self.pool,
            'spot_prices': {'WETH': Decimal(591)},
            'token_prices': {'DAI': 1.0049335, 'WETH': 596.48}
        }

    def test_swap(self):
        w_s_swap_exact_amount_in = powerpool_linear_weight_change(s_swap_exact_amount_in)
        pool_new = w_s_swap_exact_amount_in(self.params, 1, [], self.state_current, self.opcodes[0], self.opcodes[1])
        pp(pool_new)
        self.assertEqual(pool_new.total_denorm_weight, Decimal(40))
if __name__ == '__main__':
    unittest.main()
