from cadCAD.configuration import Experiment
from cadCAD.configuration.utils import config_sim
from .partial_state_update_block import partial_state_update_block

sim_config = config_sim (
    {
        'N': 1, # number of monte carlo runs
        'T': range(2491-1), # number of timesteps - 147439 is the length of uniswap_events
        'M': sys_params, # simulation parameters
    }
)

exp = Experiment()

exp.append_configs(
    sim_configs=sim_config,
    initial_state=genesis_states,
    partial_state_update_blocks=partial_state_update_block
)
