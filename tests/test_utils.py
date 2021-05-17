import pprint
import unittest
import pandas as pd
from pandas._testing import assert_frame_equal

from model.parts.utils import *
from data.utils import load_pickle


class TestUtils(unittest.TestCase):
    df = pd.DataFrame({'pool': {0:
                                    {'tokens': {'DAI': {'weight': 20, 'denorm_weight': 10, 'balance': 10000000, 'bound': True},
                                                'WETH': {'weight': 80, 'denorm_weight': 40, 'balance': 67738.6361731024, 'bound': True}},
                                     'generated_fees': 0.0, 'pool_shares': 100.0},
                                1: {
                                    'tokens': {'DAI': {'weight': 20, 'denorm_weight': 10, 'balance': 10011861.32830836, 'bound': True},
                                               'WETH': {'weight': 80, 'denorm_weight': 40, 'balance': 67720.57014558004, 'bound': True}},
                                    'generated_fees': 0.0, 'pool_shares': 100.0},
                                2: {'tokens': {'DAI': {'weight': 20, 'denorm_weight': 10, 'balance': 10027286.519776866, 'bound': True},
                                               'WETH': {'weight': 80, 'denorm_weight': 40, 'balance': 67697.1147526184, 'bound': True}},
                                    'generated_fees': 0.0, 'pool_shares': 100.0}},
                       'simulation': {0: 0, 1: 0, 2: 0},
                       'subset': {0: 0, 1: 0, 2: 0},
                       'run': {0: 1, 1: 1, 2: 1},
                       'substep': {0: 0, 1: 1, 2: 1},
                       'timestep': {0: 0, 1: 1, 2: 2}})

    def test_post_processing_pool_destructuring(self):
        result = post_processing(self.df)
        expected_df = pd.DataFrame({
            'token_dai_balance': {0: 10000000.0, 1: 10011861.32830836, 2: 10027286.519776866},
            'token_dai_weight': {0: 20, 1: 20, 2: 20},
            'token_dai_denorm_weight': {0: 10, 1: 10, 2: 10},
            'token_weth_balance': {0: 67738.6361731024, 1: 67720.57014558004, 2: 67697.1147526184},
            'token_weth_weight': {0: 80, 1: 80, 2: 80},
            'token_weth_denorm_weight': {0: 40, 1: 40, 2: 40},
            'generated_fees': {0: 0.0, 1: 0.0, 2: 0.0},
            'pool_shares': {0: 100.0, 1: 100.0, 2: 100.0},
            'simulation': {0: 0, 1: 0, 2: 0},
            'subset': {0: 0, 1: 0, 2: 0},
            'run': {0: 1, 1: 1, 2: 1},
            'substep': {0: 0, 1: 1, 2: 1},
            'timestep': {0: 0, 1: 1, 2: 2},
        })

        assert_frame_equal(result, expected_df)

    def test_post_processing_harness(self):
        """
        This is simply a harness to run postprocessing, doesn't test for anything
        """
        df = load_pickle("NB3.pickle")
        p_df = post_processing(df)
        print("END")

if __name__ == '__main__':
    unittest.main()
