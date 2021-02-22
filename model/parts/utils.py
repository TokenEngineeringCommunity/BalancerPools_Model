import pandas as pd
import typing

def unpack_column_tokens(column_tokens: pd.Series, token_symbols: typing.List[str]) -> pd.DataFrame:
    di = {}
    for symbol in token_symbols:
        di[f'token_{symbol}_balance'] = []
        di[f'token_{symbol}_denorm_weight'] = []
        di[f'token_{symbol}_weight'] = []
        for r in column_tokens:
            di[f'token_{symbol}_weight'].append(r[symbol.upper()].weight)
            di[f'token_{symbol}_denorm_weight'].append(r[symbol.upper()].denorm_weight)
            di[f'token_{symbol}_balance'].append(r[symbol.upper()].balance)
    return pd.DataFrame.from_dict(di)

def unpack_column_pool(df: pd.DataFrame) -> pd.DataFrame:
    column_pool = pd.DataFrame.from_records(df["pool"].to_list())
    token_symbols = assets_in_df(df)
    column_tokens = column_pool["tokens"]
    column_tokens_unpacked = unpack_column_tokens(column_tokens, token_symbols)
    return column_pool.assign(**column_tokens_unpacked).drop("tokens", axis=1)

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
    for symbol in token_symbols:
        symbol_low = symbol.lower()
        di[f'token_{symbol_low}_spot_price'] = []
        for r in column_spot_prices:
            di[f'token_{symbol_low}_spot_price'].append(r[symbol])
    return pd.DataFrame.from_dict(di)

def assets_in_df(df: pd.DataFrame) -> typing.List[str]:
    assets = list(df.pool[0]["tokens"].keys())
    assets.sort()
    assets = [a.lower() for a in assets]
    return assets

def calc_token_x_value(df: pd.DataFrame) -> pd.DataFrame:
    symbols = assets_in_df(df)
    di = {}
    for s in symbols:
        di[f'token_{s}_value'] = df[f'token_{s}_balance'].astype(float) * df[f'token_{s}_price']
    return pd.DataFrame.from_dict(di)

def post_processing(df: pd.DataFrame) -> pd.DataFrame:
    unpacked_column_pool = unpack_column_pool(df)
    unpacked_column_token_prices = unpack_column_token_prices(df)
    unpacked_column_spot_prices = unpack_column_spot_prices(df)

    df = df.assign(**unpacked_column_pool).assign(**unpacked_column_token_prices).assign(**unpacked_column_spot_prices)

    # Convert change_datetime from str to datetime
    df["change_datetime"] = pd.to_datetime(df["change_datetime"], utc=True)

    # Calculate token_{x}_value columns
    token_x_value = calc_token_x_value(df)
    df = df.assign(**token_x_value)

    # Calculate TVL column
    symbols = assets_in_df(df)
    token_value_columns = [f'token_{s}_value' for s in symbols]
    column_tvl = df[token_value_columns].sum(axis=1)
    df = df.assign(tvl=column_tvl)

    # Calculate total_token_balances
    token_balance_columns = [f'token_{s}_balance' for s in symbols]
    column_total_token_balances = df[token_balance_columns].sum(axis=1)
    df = df.assign(total_token_balances=column_total_token_balances)

    return df
