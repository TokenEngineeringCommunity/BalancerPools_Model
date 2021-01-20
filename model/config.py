from cadCAD.configuration.utils import config_sim

parameters = {
    'swap_fee': Decimal(0.1)
}

sim_config = config_sim(
    {
        'N': 1,  # number of monte carlo runs
        'T': range(2491 - 1),  # number of timesteps - 147439 is the length of uniswap_events
        'M': parameters,  # simulation parameters
    }
)

