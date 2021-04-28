import unittest
import pytest
import pandas as pd
from cadCAD.configuration.utils import config_sim

from model.genesis_states import generate_initial_state
from model.partial_state_update_block import generate_partial_state_update_blocks
from model.sim_runner import *
from model.parts.utils import post_processing

"""
NB0-SanityCheck.ipynb is meant to compare REPLAY_OUTPUT, SIMPLIFIED and CONTRACT_CALL modes. And this comparison is to be done by humans.
This sanity check OTOH is to ensure consistent behaviour when code is refactored. However, there might be fluctuations in the results between commits.
"""

class TestSimulationConsistency(unittest.TestCase):
    def test_simulation_consistency(self):
        """
        Copied from NB1-PoolExploration-0x8b6
        """
        # Spot price reference must be a symbol of a token in the pool in ALL_CAPS, you can ignore the spot price parameter for the simulations in this notebook.
        parameters = {
            'spot_price_reference': ['DAI'],
            'decoding_type': ['SIMPLIFIED']
        }

        initial_values = generate_initial_state(initial_values_json='../data/0x8b6e6e7b5b3801fed2cafd4b22b8a16c2f2db21a-initial_pool_states-prices.json', spot_price_base_currency=parameters['spot_price_reference'][0])

        result = generate_partial_state_update_blocks('../data/0x8b6e6e7b5b3801fed2cafd4b22b8a16c2f2db21a-actions-prices.json')
        partial_state_update_blocks = result['partial_state_update_blocks']

        steps_number = result['steps_number']
        sim_config = config_sim(
            {
                'N': 1,  # number of monte carlo runs
                'T': range(steps_number - 1),  # number of timesteps
                'M': parameters,  # simulation parameters
            }
        )

        df = run(initial_values, partial_state_update_blocks, sim_config)
        p_df = post_processing(df, include_spot_prices=False)
        p_df_ref = pd.read_pickle("0x8b6-reference-p_df-commit-886b55321957449d6cbf3afafdf57b9e64a8cadb.pickle")
        if not p_df_ref.equals(p_df):
            for i in range(len(p_df)):
                if not p_df_ref.loc[i].equals(p_df.loc[i]):
                    print("Discrepancy starts at timestep", i)
                    refrow = p_df_ref.loc[i]
                    row = p_df.loc[i]
                    print(refrow.compare(row))
                    break
        final_row = len(p_df)-1
        print("Discrepancy at end of simulation", final_row)
        print(p_df_ref.iloc[final_row].compare(p_df.iloc[final_row]))
