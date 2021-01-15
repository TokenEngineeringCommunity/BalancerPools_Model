"""
Model parameters.
"""

# These are the initial conditions of the DAI-ETH Uniswap instance - https://etherscan.io/address/0x09cabEC1eAd1c0Ba254B09efb3EE13841712bE14
initial_values = {
    'pool': {
        'tokens': {
            'DAI': {
                'weight': 20,
                'balance': 10000000
            },
            'WETH': {
                'weight': 80,
                'balance': 67738.636173102396002749
            }
        },
        'generated_fees': 0.0,
        'pool_shares': 100.0
    },
}


### Parameters

# These are the parameters of Uniswap that represent the fee collected on each swap. Notice that these are hardcoded in the Uniswap smart contracts, but we model them as parameters in order to be able to do A/B testing and parameter sweeping on them in the future.

sys_params = {
    'swap_fee': [0.1],
}
