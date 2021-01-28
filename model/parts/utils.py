
from pandas import DataFrame


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

        idx_token_values = row.get('token_values')
        if idx_token_values is not None:
            for token in idx_token_values:
                append_to_list(sim_dict, f'token_{token.lower()}_value', idx_token_values[token])

        rest_keys = list(filter(lambda key: key != 'token_values' and key != 'pool', df.columns))
        for key in rest_keys:
            append_to_list(sim_dict, key, row[key])
    processed_df = DataFrame.from_dict(sim_dict)
    return processed_df
