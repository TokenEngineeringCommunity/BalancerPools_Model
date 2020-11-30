import unittest
from decimal import Decimal

from model.balancer_pool import BalancerPool


class TestBalancerPool(unittest.TestCase):
    def test_bind_equal_weights(self):
        pool = BalancerPool()
        pool.bind('WETH', Decimal('50'), 5)
        pool.bind('ETHIX', Decimal('20'), 5)
        pool.bind('DAI', Decimal('10000'), 5)
        assert pool.get_num_tokens() == 3
        assert pool.get_total_denorm_weight() == 15
        assert pool.get_denorm_weight('WETH') == 5
        self.assertAlmostEqual(pool.get_normal_weight('WETH'), Decimal('0.333333333333333333'))
        assert pool.get_balance('ETHIX') == Decimal('20')

    @unittest.skip("need test data")
    def test_unbind(self):
        pass

    def test_join_pool(self):
        pool = BalancerPool()
        pool.bind('WETH', Decimal('50'), 5)
        pool.bind('ETHIX', Decimal('20'), 5)
        pool.bind('DAI', Decimal('10000'), 5)
        pool_out = pool.join_pool(Decimal('5'), {'WETH': Decimal('Infinity'), 'ETHIX': Decimal('Infinity'), 'DAI': Decimal('Infinity')})

        self.assertAlmostEqual(pool.get_balance('DAI'), Decimal('10500'))
        self.assertAlmostEqual(pool.get_balance('ETHIX'), Decimal('21.00'))
        self.assertAlmostEqual(pool.get_balance('WETH'), Decimal('52.50'))
        self.assertEqual(pool_out, Decimal('5'))
        # NOTE: In balancer, user balances are pulled
        # assert.equal(22.5, fromWei(userWethBalance));

    @unittest.skip("need test data")
    def test_exit_pool(self):
        pass

    def test_get_spot_price(self):
        pool = BalancerPool()
        pool.bind('WETH', Decimal('52.5'), 5)
        pool.bind('ETHIX', Decimal('21'), 5)
        pool.bind('DAI', Decimal('10500'), 5)
        pool.set_swap_fee(Decimal('0.003'))
        self.assertAlmostEqual(pool.get_spot_price_sans_fee('DAI', 'WETH'), Decimal('200'))
        self.assertAlmostEqual(pool.get_spot_price('DAI', 'WETH'), Decimal('200.6018054162487462'))

    def test_swap_exact_amount_in(self):
        pool = BalancerPool()
        pool.bind('WETH', Decimal('52.5'), 5)
        pool.bind('ETHIX', Decimal('21'), 5)
        pool.bind('DAI', Decimal('10500'), 5)
        pool.set_swap_fee(Decimal('0.003'))
        # 2.5 WETH -> DAI
        # NOTE: maxes not needed
        result = pool.swap_exact_amount_in('WETH', Decimal('2.5'), 'DAI', Decimal('475'), Decimal('200'))
        print(result)
        self.assertAlmostEqual(result.token_amount_out, Decimal('475.905805337091423'))






if __name__ == '__main__':
    unittest.main()
