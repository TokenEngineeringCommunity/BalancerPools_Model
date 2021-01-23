import unittest
from unittest.mock import patch

import pandas

from model.parts.system_policies import p_action_decoder, p_external_price_feed_decoder
'''
mock_df = pandas.Dataframe([
    {
        "unixtimestamp": "1607348054",
        "datetime": "2020-12-07 13:34:14",
        "tokens": {
            "DAI": [
                {
                    "from": "0x9d7c587709205fe908fac2be6df9bc15c4b56b37",
                    "to": "0x8b6e6e7b5b3801fed2cafd4b22b8a16c2f2db21a",
                    "value": 10000000.0
                }
            ],
            "WETH": [
                {
                    "from": "0x9d7c587709205fe908fac2be6df9bc15c4b56b37",
                    "to": "0x8b6e6e7b5b3801fed2cafd4b22b8a16c2f2db21a",
                    "value": 67738.6361731024
                }
            ],
            "BPT": [
                {
                    "from": "0x0000000000000000000000000000000000000000",
                    "to": "0x8b6e6e7b5b3801fed2cafd4b22b8a16c2f2db21a",
                    "value": 100.0
                },
                {
                    "from": "0x8b6e6e7b5b3801fed2cafd4b22b8a16c2f2db21a",
                    "to": "0x9d7c587709205fe908fac2be6df9bc15c4b56b37",
                    "value": 100.0
                }
            ]
        },
        "index": 0,
        "action": {
            "pool_amount_out": 100.0,
            "tokens_in": {
                "DAI": 10000000.0,
                "WETH": 67738.6361731024
            },
            "type": "join"
        },
        "tx_hash": "0xb5875c4663360b8d311ddef2b394e64aae74a362332ae0212eea02c868ced7c3",
        "timestep": 0
    },
    {
        "unixtimestamp": "1607348406",
        "datetime": "2020-12-07 13:40:06",
        "tokens": {
            "DAI": [
                {
                    "from": "0x0000000000007f150bd6f54c40a34d7c3d5e9f56",
                    "to": "0x8b6e6e7b5b3801fed2cafd4b22b8a16c2f2db21a",
                    "value": 11861.328308361
                }
            ],
            "WETH": [
                {
                    "from": "0x8b6e6e7b5b3801fed2cafd4b22b8a16c2f2db21a",
                    "to": "0x0000000000007f150bd6f54c40a34d7c3d5e9f56",
                    "value": 20.021734699893457
                }
            ]
        },
        "index": 1,
        "action": {
            "type": "swap",
            "token_in": "DAI",
            "token_amount_in": 11861.328308361,
            "token_out": "WETH",
            "token_amount_out": 20.021734699893457
        },
        "tx_hash": "0x0319e9eacb5c6ec9905ccdda0e0d9971ac22410bfabf6f32212608d5f0565aef",
        "timestep": 352
    }])
'''

class TestSystemPolicies(unittest.TestCase):

    @unittest.skip(reason='problems with df mocking')
    @patch('model.parts.system_policies.pd.read_json')
    def test_action_for_timestep(self, df_fake):
        #df_fake.return_value = mock_df
        result = p_action_decoder(params={}, step=11, history={}, current_state={'timestep': 352})
        pool_update = result['pool_update']
        action = pool_update.loc[1]
        self.assertDictEqual(action, {
            "type": "swap",
            "token_in": "DAI",
            "token_amount_in": 11861.328308361,
            "token_out": "WETH",
            "token_amount_out": 20.021734699893457
        })

    @unittest.skip(reason='problems with df mocking')
    @patch('model.parts.system_policies.pd.read_json')
    def test_no_action_for_timestep(self, df_fake):
        #df_fake.return_value = mock_df
        result = p_action_decoder(params={}, step=11, history={}, current_state={'timestep': 11})
        pool_update = result.get('pool_update')
        self.assertIsNone(pool_update)


    # @patch('model.parts.system_policies.pd.read_json')
    def test_price_feed(self):
        #df_fake.return_value = mock_df
        result = p_external_price_feed_decoder(params={}, step=3, history={}, current_state={'timestep': 3})
        print(result)
        self.assertEqual(1,2)





if __name__ == '__main__':
    unittest.main()
