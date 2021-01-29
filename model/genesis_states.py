"""
Model parameters.
"""

# These are the initial conditions of the DAI-ETH Uniswap instance - https://etherscan.io/address/0x09cabEC1eAd1c0Ba254B09efb3EE13841712bE14
initial_values = {
    'pool': {
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
    },
    'action_type': 'pool_creation',
    'change_datetime': '2020-12-07 13:34:14',
    # Close value of first item from COINBASE_<token>USD_5.csv
    'token_prices': {
        'DAI': 1.004832,
        'WETH': 596.75
    }
}
