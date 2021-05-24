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

    def test_swap(self):
        dai586 = TokenAmount(symbol='DAI', amount=Decimal(586.651036))
        weth1 = TokenAmount(symbol='WETH', amount=Decimal(1))
        self.opcodes = (SwapExactAmountInInput(token_in=weth1, min_token_out=dai586), SwapExactAmountInOutput(token_out=dai586))

        self.pool = Pool(
            tokens={
                'DAI': Token(denorm_weight=10, balance=Decimal(100000), bound=True),
                'WETH': Token(denorm_weight=40, balance=Decimal(677.6361731), bound=True)
            },
            generated_fees={},
            shares=Decimal(100),
            swap_fee=Decimal(0.0025),
            denorm_weight_constant=50
        )
        self.state_current = {
            'pool': self.pool,
            'spot_prices': {
                'WETH': {'DAI': Decimal('0.001698336273433583836840493148')},
                'DAI': {'WETH': Decimal('591.7666768454633867581667000')},
            },
            'token_prices': {'DAI': 1, 'WETH': 599}
        }

        w_s_swap_exact_amount_in = powerpool_linear_weight_change(s_swap_exact_amount_in)
        pool_new = w_s_swap_exact_amount_in(self.params, 1, [], self.state_current, self.opcodes[0], self.opcodes[1])
        pp(pool_new)
        self.assertEqual(pool_new.total_denorm_weight, Decimal(50))
if __name__ == '__main__':
    unittest.main()
