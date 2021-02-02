
from pandas import DataFrame

# grab list of tokens (symbols) in the pool/result data frame
#tlist = [] 

def append_to_list(dictionary, key, value):
    if dictionary.get(key) is None:
        dictionary[key] = []
    dictionary[key].append(value)

def post_processing(df: DataFrame) -> DataFrame:
    sim_dict = {}
    for i, row in df.iterrows():
        idx_pool = row['pool']
        for token in idx_pool['tokens']:
            append_to_list(sim_dict, f'token_{token.lower()}_balance', idx_pool['tokens'][token]['balance'])
            append_to_list(sim_dict, f'token_{token.lower()}_weight', idx_pool['tokens'][token]['weight'])
            append_to_list(sim_dict, f'token_{token.lower()}_denorm_weight', idx_pool['tokens'][token]['denorm_weight'])
        append_to_list(sim_dict, 'generated_fees', idx_pool['generated_fees'])
        append_to_list(sim_dict, 'pool_shares', idx_pool['pool_shares'])

        idx_token_prices = row.get('token_prices')
        if idx_token_prices is not None:
            for token in idx_token_prices:
                append_to_list(sim_dict, f'token_{token.lower()}_price', idx_token_prices[token])

        idx_spot_prices = row.get('spot_prices')
        if idx_spot_prices is not None:
            for token in idx_spot_prices:
                append_to_list(sim_dict, f'token_{token.lower()}_spot_price', idx_spot_prices[token])

        rest_keys = list(filter(lambda key: key != 'token_prices' and key != 'pool' and key != 'spot_prices', df.columns))
        for key in rest_keys:
            append_to_list(sim_dict, key, row[key])

    processed_df = DataFrame.from_dict(sim_dict)

     # create new column for token_k_values (value=balance*price)
    for i in tlist:
        df[f'token_{i}_value'] = df[f'token_{i}_balance']*df[f'token_{i}_price']

    # create new column for TVL (sum of all token_k_values)
    for i in tlist: 
        a = df[f'token_{tlist[0]}_value'] #needs refactoring, so that we not only pick a+b but all tokens (up to 8) values
        b = df[f'token_{tlist[1]}_value']
        df['TVL_total_token_value'] = a + b

    return processed_df
