import unittest
from decimal import Decimal
from unittest.case import skip

from model.balancer_constants import EXIT_FEE
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

    def test_exit_pool(self):
        pool = BalancerPool(initial_pool_supply=Decimal('135.224857816660897462'))
        pool.bind('DAI', Decimal('63.139999999999999949'), Decimal('2'))
        pool.bind('ETHIX', Decimal('613.124321062160530356'), Decimal('18'))
        pool.set_swap_fee(Decimal('0.001'))
        pool_amount_in = Decimal('5')
        results = pool.exit_pool(pool_amount_in=pool_amount_in, min_amounts_out={
          'DAI': Decimal('0'),
          'ETHIX': Decimal('0')
        })
        print(results)
        self.assertAlmostEqual(results['DAI'], Decimal('2.334629927494758091'))
        self.assertAlmostEqual(results['ETHIX'], Decimal('22.670547817969981334'))
        self.assertAlmostEqual(pool.pool_token_supply, Decimal('130.224857816660897462'))
        self.assertAlmostEqual(results['exit_fee_pool_token'], pool_amount_in * EXIT_FEE)


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
        pool.bind('WETH', Decimal('4'), Decimal('10'))
        pool.bind('ETHIX', Decimal('12'), Decimal('10'))
        pool.set_swap_fee(Decimal('0.001'))
        # NOTE: maxes not needed
        result = pool.swap_exact_amount_in(token_in='WETH',
                                           token_amount_in=Decimal('2'),
                                           token_out='ETHIX',
                                           min_amount_out=Decimal('0'),
                                           max_price=Decimal('200000'))
        print(result)
        self.assertAlmostEqual(result.token_amount_out, Decimal('3.997332444148049352'))
        self.assertAlmostEqual(result.spot_price_after, Decimal('0.7505005005005005'))
        # TODO assert pool balances

    def test_swap_exact_amount_out(self):
        pool = BalancerPool()
        pool.bind('WETH', Decimal('4'), Decimal('10'))
        pool.bind('ETHIX', Decimal('12'), Decimal('10'))
        pool.set_swap_fee(Decimal('0.001'))
        # NOTE: maxes not needed
        result = pool.swap_exact_amount_out(token_in='ETHIX',
                                            max_amount_in=Decimal('2999999999999999999'),
                                            token_out='WETH',
                                            token_amount_out=Decimal('1'),
                                            max_price=Decimal('20099999999999999000'))
        print(result)
        self.assertAlmostEqual(result.token_amount_in, Decimal('4.004004004004004'))
        self.assertAlmostEqual(result.spot_price_after, Decimal('5.340008009344012012'))

    def test_join_swap_extern_amount_in(self):
        pool = BalancerPool(initial_pool_supply=Decimal('132.915130375973322493'))
        pool.bind('WETH', Decimal('53.139999999999999949'), Decimal('2'))
        pool.bind('ETHIX', Decimal('613.124321062160530356'), Decimal('18'))
        swap_fee = Decimal('0.001')
        pool.set_swap_fee(swap_fee)
        t_ai = Decimal('10')

        p_ao = pool.join_swap_extern_amount_in(token_in='WETH', token_amount_in=t_ai, min_pool_amount_out=Decimal('0'))
        self.assertAlmostEqual(p_ao, Decimal('2.309727440687574969'))
        self.assertAlmostEqual(pool.pool_token_supply, Decimal('135.224857816660897462'))

    def test_join_join_swap_pool_amount_out(self):
        pool = BalancerPool(initial_pool_supply=Decimal('100'))
        pool.bind('WETH', Decimal('4'), Decimal('10'))
        pool.bind('DAI', Decimal('12'), Decimal('11'))
        swap_fee = Decimal('0.001')
        pool.set_swap_fee(swap_fee)
        p_ao = Decimal('2.2')
        t_ai = pool.join_swap_pool_amount_out(token_in='DAI', pool_amount_out=p_ao, max_amount_in=Decimal('1000'))
        self.assertAlmostEqual(pool.pool_token_supply, Decimal('102.2'))
        self.assertAlmostEqual(t_ai, Decimal('0.509279173873455029'))
        self.assertAlmostEqual(pool.get_balance('DAI'), Decimal('12.509279173873455029'))
        self.assertAlmostEqual(pool.get_balance('WETH'), Decimal('4'))



if __name__ == '__main__':
    unittest.main()
