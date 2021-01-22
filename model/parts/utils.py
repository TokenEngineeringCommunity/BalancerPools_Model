
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
        append_to_list(sim_dict, 'simulation', row['simulation'])
        append_to_list(sim_dict, 'subset', row['subset'])
        append_to_list(sim_dict, 'run', row['run'])
        append_to_list(sim_dict, 'substep', row['substep'])
        append_to_list(sim_dict, 'timestep', row['timestep'])

    processed_df = DataFrame.from_dict(sim_dict)
    return processed_df
