import pandas as pd
import typing

def get_param(params: typing.Dict, key: str):
    # When only 1 param this happens
    if isinstance(params, list):
        # 1 param
        return params[0][key]
    else:
        # Parameter sweep
        return params[key]

def unpack_column_tokens(column_tokens: pd.Series, token_symbols: typing.List[str], pool_denorm_weight_constant: int) -> pd.DataFrame:
    di = {}
    for symbol in token_symbols:
        di[f'token_{symbol}_balance'] = []
        di[f'token_{symbol}_denorm_weight'] = []
        di[f'token_{symbol}_weight'] = []
        for r in column_tokens:
            di[f'token_{symbol}_weight'].append(r[symbol.upper()].denorm_weight / pool_denorm_weight_constant)
            di[f'token_{symbol}_denorm_weight'].append(r[symbol.upper()].denorm_weight)
            di[f'token_{symbol}_balance'].append(r[symbol.upper()].balance)
    return pd.DataFrame.from_dict(di).astype('float64')


def unpack_column_generated_fees(column_fees: pd.Series, token_symbols: typing.List[str]) -> pd.DataFrame:
    di = {}
    for symbol in token_symbols:
        di[f'generated_fees_{symbol}'] = []
        for r in column_fees:
            di[f'generated_fees_{symbol}'].append(r[symbol.upper()])
    return pd.DataFrame.from_dict(di)


def unpack_column_shares(column_shares: pd.Series):
    di = {f'pool_shares': []}
    for r in column_shares:
        di[f'pool_shares'].append(r)
    return pd.DataFrame.from_dict(di)


def unpack_column_pool(df: pd.DataFrame) -> pd.DataFrame:
    token_symbols = assets_in_df(df)
    # TODO: the Pool.as_dict() interface is heavily relied on here (except for
    # the line above) because postprocessing was written back when pool the
    # state variable was a dict
    list_of_pool_objs = df["pool"].to_list()
    pool_denorm_weight_constant = list_of_pool_objs[0].denorm_weight_constant
    list_of_pool_dicts = [p.as_dict() for p in list_of_pool_objs]
    column_pool = pd.DataFrame.from_records(list_of_pool_dicts)

    column_shares = column_pool["shares"]
    column_shares = unpack_column_shares(column_shares)

    column_tokens = column_pool["tokens"]
    column_tokens_unpacked = unpack_column_tokens(column_tokens, token_symbols, pool_denorm_weight_constant)


    column_fees = column_pool['generated_fees']
    column_generated_fees_unpacked = unpack_column_generated_fees(column_fees, token_symbols)
    return column_pool.assign(**column_tokens_unpacked).assign(**column_generated_fees_unpacked).assign(**column_shares).drop("tokens", axis=1)


def unpack_column_token_prices(df: pd.DataFrame) -> pd.DataFrame:
    column_token_prices = df["token_prices"]
    token_symbols = assets_in_df(df)
    di = {}
    for symbol in token_symbols:
        di[f'token_{symbol}_price'] = []
        for r in column_token_prices:
            di[f'token_{symbol}_price'].append(r[symbol.upper()])
    return pd.DataFrame.from_dict(di)



# At this point I should generalize the "unpacking" pattern, but then it'd be even harder to follow once I've forgotten everything
def unpack_column_spot_prices(df: pd.DataFrame) -> pd.DataFrame:
    column_spot_prices = df.spot_prices
    # Can't assets_in_df() here because this column might not include spot_prices for all assets in df (why?)
    token_symbols = list(column_spot_prices[0].keys())
    token_symbols.sort()
    di = {}
    for token_in in token_symbols:
        token_in_low = token_in.lower()
        tokens_out = token_symbols.copy()
        tokens_out.remove(token_in)
        for token_out in tokens_out:
            token_out_low = token_out.lower()
            di[f'token_spot_price_{token_in_low}_{token_out_low}'] = []
            for r in column_spot_prices:
                price = r[token_in][token_out]
                di[f'token_spot_price_{token_in_low}_{token_out_low}'].append(price)
    return pd.DataFrame.from_dict(di).astype('float64')


def assets_in_df(df: pd.DataFrame) -> typing.List[str]:
    assets = list(df.pool[0].tokens.keys())
    assets.sort()
    assets = [a.lower() for a in assets]
    return assets


def calc_token_x_value(df: pd.DataFrame) -> pd.DataFrame:
    symbols = assets_in_df(df)
    di = {}
    for s in symbols:
        di[f'token_{s}_value'] = df[f'token_{s}_balance'].astype(float) * df[f'token_{s}_price'].astype(float)
    return pd.DataFrame.from_dict(di)


def post_processing(df: pd.DataFrame, include_spot_prices=False) -> pd.DataFrame:
    unpacked_column_pool = unpack_column_pool(df)
    unpacked_column_token_prices = unpack_column_token_prices(df)

    df = df.assign(**unpacked_column_pool).assign(**unpacked_column_token_prices)
    if include_spot_prices:
        unpacked_column_spot_prices = unpack_column_spot_prices(df)
        df = df.assign(**unpacked_column_spot_prices)

    # Convert change_datetime from str to datetime, other columns to float64
    df["change_datetime"] = pd.to_datetime(df["change_datetime"], utc=True)
    df = df.astype({"shares": "float64", "swap_fee": "float64"})

    # Calculate token_{x}_value columns
    token_x_value = calc_token_x_value(df)
    df = df.assign(**token_x_value)

    # Calculate TVL column
    symbols = assets_in_df(df)
    token_value_columns = [f'token_{s}_value' for s in symbols]
    column_tvl = df[token_value_columns].sum(axis=1)
    df = df.assign(tvl=column_tvl)

    # Calculate Invariant column
    df['invariant'] = 1
    for s in symbols:
        df['invariant'] *= (df[f'token_{s}_balance'] ** df[f'token_{s}_weight'])

    # Calculate total_token_balances
    token_balance_columns = [f'token_{s}_balance' for s in symbols]
    column_total_token_balances = df[token_balance_columns].sum(axis=1)
    df = df.assign(total_token_balances=column_total_token_balances)

    # Convert generated_fees_(token) columns from str or Decimal to float64
    generated_fees_columns = [f'generated_fees_{s}' for s in symbols]
    for generated_fee_col in generated_fees_columns: df[generated_fee_col] = df[generated_fee_col].astype('float64')
    return df
