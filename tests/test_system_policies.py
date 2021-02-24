import unittest
from decimal import Decimal

from model.parts.system_policies import p_action_decoder

class TestSystemPolicies(unittest.TestCase):

    @unittest.skip(reason='skipping until refactor to better mock df')
    # @patch('model.parts.system_policies.pd.read_json')
    def test_action(self):
        # df_fake.return_value = mock_df
        result = p_action_decoder(params={}, step=11, history={}, current_state={'timestep': 352})
        action = result['pool_update']
        '''
        self.assertDictEqual(action, {
            "type": "swap",
            "token_in": "DAI",
            "token_amount_in": 11861.328308361,
            "token_out": "WETH",
            "token_amount_out": 20.021734699893457,
            "datetime": "2020-12-09 10:32:00"
        })
        '''
        change_datetime = result['change_datetime']

        self.assertEqual(change_datetime, '2020-12-09 10:32:00')

    def test_swap_txhash_0x0319e9eacb5c6ec9905ccdda0e0d9971ac22410bfabf6f32212608d5f0565aef(self):
        pool_state_11405970 = {
            'tokens': {
                'DAI': {
                    'weight': 20,
                    'denorm_weight': 10,
                    'balance': 10000000,
                    'bound': True
                },
                'WETH': {
                    'weight': 80,
                    'denorm_weight': 40,
                    'balance': 67738.636173102396002749,
                    'bound': True
                }
            },
            'generated_fees': 0.0,
            'pool_shares': 100.0
        }
        initial_state = {
            'pool': pool_state_11405970,
            'timestep': 0,
        }
        params = [{
            'swap_fee': Decimal(0.0025)  # reference value from archive node
        }]
        result = p_action_decoder(params=params, step=1, history={}, current_state=initial_state)

        pool_state_11405998 = {
            'tokens': {
                'DAI': {
                    'weight': 20,
                    'denorm_weight': 10,
                    'balance': 10011861.328308360999600128,
                    'bound': True
                },
                'WETH': {
                    'weight': 80,
                    'denorm_weight': 40,
                    'balance': 67718.614438402502546905,
                    'bound': True
                }
            },
            'generated_fees': 0.0,
            'pool_shares': 100.0
        }
        # Reference Values (on the right) obtained from an archive node. The results from the simulation may be missing some decimal places.
        # 6 decimal place accuracy is acceptable, but assertAlmostEqual compares to 7 decimal digits by default (at least I assume that's what "places" means)
        # https://docs.python.org/3/library/unittest.html#unittest.TestCase.assertAlmostEqual
        self.assertEqual(result['pool_update']['tokens']['DAI']['balance'],
                         pool_state_11405998['tokens']['DAI']['balance'])
        self.assertAlmostEqual(result['pool_update']['tokens']['WETH']['balance'],
                               pool_state_11405998['tokens']['WETH']['balance'])

    def test_join_swap_txhash_0xf31a60f963a54f1ed77d55680b073549767ecccdd83c7721f3b6d6039bec5394(self):
        pool_state_11411173 = {
            'tokens': {
                'DAI': {
                    'weight': 20,
                    'denorm_weight': 10,
                    'balance': 9872549.777138393124800348,
                    'bound': True
                },
                'WETH': {
                    'weight': 80,
                    'denorm_weight': 40,
                    'balance': 67958.947376965836020558,
                    'bound': True
                }
            },
            'generated_fees': 0.0,
            'pool_shares': 100.0
        }
        initial_state = {
            'pool': pool_state_11411173,
            'timestep': 103,
        }
        params = [{
            'swap_fee': Decimal(0.0025)  # reference value from archive node
        }]
        result = p_action_decoder(params=params, step=1, history={}, current_state=initial_state)

        pool_state_11411174 = {
            'tokens': {
                'DAI': {
                    'weight': 20,
                    'denorm_weight': 10,
                    'balance': 9872549.777138393124800348,
                    'bound': True
                },
                'WETH': {
                    'weight': 80,
                    'denorm_weight': 40,
                    'balance': 67985.688978381434696622,
                    'bound': True
                }
            },
            'generated_fees': 0.0,
            'pool_shares': 100.0314627351852568
        }
        self.assertEqual(result['pool_update']['tokens']['DAI']['balance'],
                         pool_state_11411174['tokens']['DAI']['balance'])
        self.assertEqual(result['pool_update']['tokens']['WETH']['balance'],
                         pool_state_11411174['tokens']['WETH']['balance'])
        self.assertAlmostEqual(result['pool_update']['pool_shares'], pool_state_11411174['pool_shares'])

    def test_join_txhash_0xfbaa0d59fc39ea9201d0d105585fa1f88d011f76296b42cd6e13bb65c47e8ab6(self):
        pool_state_11484895 = {
            'tokens': {
                'DAI': {
                    'weight': 20,
                    'denorm_weight': 10,
                    'balance': 10932236.880826812338871069,
                    'bound': True
                },
                'WETH': {
                    'weight': 80,
                    'denorm_weight': 40,
                    'balance': 66336.857387246365758182,
                    'bound': True
                }
            },
            'generated_fees': 0.0,
            'pool_shares': 100.006040928440959949
        }
        initial_state = {
            'pool': pool_state_11484895,
            'timestep': 1994,  # 1995 -1
        }
        params = [{
            'swap_fee': Decimal(0.0025)  # reference value from archive node
        }]
        result = p_action_decoder(params=params, step=1, history={}, current_state=initial_state)

        pool_state_11484896 = {
            'tokens': {
                'DAI': {
                    'weight': 20,
                    'denorm_weight': 10,
                    'balance': 10932401.686991734982597079,
                    'bound': True
                },
                'WETH': {
                    'weight': 80,
                    'denorm_weight': 40,
                    'balance': 66337.857431718342619721,
                    'bound': True
                }
            },
            'generated_fees': 0.0,
            'pool_shares': 100.007548544151649414
        }
        self.assertEqual(result['pool_update']['tokens']['DAI']['balance'],
                         pool_state_11484896['tokens']['DAI']['balance'])
        self.assertEqual(result['pool_update']['tokens']['WETH']['balance'],
                         pool_state_11484896['tokens']['WETH']['balance'])
        self.assertEqual(result['pool_update']['pool_shares'], pool_state_11484896['pool_shares'])

    def test_exit_swap_txhash_0x43fdd919d240ca7c69267219a53c0b7fdf805c27fc43f1c3133f0c369fcb1200(self):
        pool_state_11415302 = {
            'tokens': {
                'DAI': {
                    'weight': 20,
                    'denorm_weight': 10,
                    'balance': 9415046.933427339711378381,
                    'bound': True
                },
                'WETH': {
                    'weight': 80,
                    'denorm_weight': 40,
                    'balance': 68804.617403193602302615,
                    'bound': True
                }
            },
            'generated_fees': 0.0,
            'pool_shares': 100.0314627351852568
        }
        initial_state = {
            'pool': pool_state_11415302,
            'timestep': 247,  # 1995 -1
        }
        params = [{
            'swap_fee': Decimal(0.0025)  # reference value from archive node
        }]
        result = p_action_decoder(params=params, step=1, history={}, current_state=initial_state)

        pool_state_11415303 = {
            'tokens': {
                'DAI': {
                    'weight': 20,
                    'denorm_weight': 10,
                    'balance': 9415046.933427339711378381,
                    'bound': True
                },
                'WETH': {
                    'weight': 80,
                    'denorm_weight': 40,
                    'balance': 68777.580734776983569267,
                    'bound': True
                }
            },
            'generated_fees': 0.0,
            'pool_shares': 100,
        }
        self.assertEqual(result['pool_update']['tokens']['DAI']['balance'],
                         pool_state_11415303['tokens']['DAI']['balance'])
        self.assertAlmostEqual(result['pool_update']['tokens']['WETH']['balance'],
                         pool_state_11415303['tokens']['WETH']['balance'])
        self.assertAlmostEqual(result['pool_update']['pool_shares'], pool_state_11415303['pool_shares'])


if __name__ == '__main__':
    unittest.main()
