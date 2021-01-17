import unittest

from model.parts.system_policies import p_action_decoder


class TestSystem(unittest.TestCase):

    def test_p_action_decoder(self):
        action = p_action_decoder({}, 0 , {}, { 'timestep': 0})
        self.assertDictEqual(action, {
            "type": "swap",
            "token_in": "DAI",
            "token_amount_in": "11861.328308360999600128",
            "token_out": "WETH",
            "token_amount_out": "20.021734699893455844"
        })



if __name__ == '__main__':
    unittest.main()
