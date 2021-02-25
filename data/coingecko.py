import typing
import collections
import pandas as pd
from pycoingecko import CoinGeckoAPI
from datetime import datetime, timedelta, timezone
from utils import load_json
cg = CoinGeckoAPI()
symbol_id_map = {}

def initialize_coingecko_api():
    cg_coins_list = cg.get_coins_list()

    for c in cg_coins_list:
        symbol_id_map[c['symbol']] = c['id']

def tidy_up_prices(prices: typing.List[typing.List]) -> typing.List[typing.Tuple]:
    """
    input [[timestamp_ms, price_avg], [..]...] (90d ago -> now, 180d ago -> 90d ago, 270d ago -> 180d ago)
    output [(datetime(timestamp_s), price_avg), (..)...] (sorted by timestamp)
    """
    p2 = [(datetime.fromtimestamp(int(p[0]/1000), timezone.utc), p[1]) for p in prices]
    p2.sort(key=lambda p: p[0])

    return p2

def get_90d_of_hourly_prices(coin_symbol: str, base: str, to_timestamp: datetime):
    """
    Coingecko only gives us hourly data for 90d at a time, more than that and it's daily prices.
    """
    coin_id = symbol_id_map[coin_symbol]
    delta = timedelta(days=90)
    res = cg.get_coin_market_chart_range_by_id(coin_id, base, int((to_timestamp-delta).timestamp()), int(to_timestamp.timestamp()))
    return res['prices']

def get_complete_hourly_prices(coin_symbol: str, base: str):
    """
    Request 90d at a time from Coingecko to keep getting hourly data for the entire life of the coin
    """
    all_prices = []
    delta = 0
    while True:
        answer = get_90d_of_hourly_prices(coin_symbol, base, datetime.now() - timedelta(days=delta))
        if not answer:
            break
        delta += 90
        all_prices.extend(answer)
    return tidy_up_prices(all_prices)

def only_prices_after_initial_state(prices: typing.List[typing.Tuple], initial_state_datetime: str) -> typing.List[typing.Tuple]:
    initial_state_datetime = datetime.fromisoformat(initial_state_datetime)
    for i, p in enumerate(prices):
        if p[0] > initial_state_datetime:
            return prices[i:]
    raise Exception("There is no price data available after the simulation's starting point")

def load_coingecko_prices_json(path: str):
    prices = load_json(path)
    prices = [(datetime.fromisoformat(p[0]), p[1]) for p in prices]
    return prices

def dataframeize(prices: typing.List[typing.Tuple], column_name: str) -> pd.DataFrame:
    df = pd.DataFrame(prices)
    df.columns = ["timestamp", column_name]
    return df

def merge_feeds_into_dataframe(feeds: collections.OrderedDict) -> pd.DataFrame:
    df = pd.DataFrame(columns=["timestamp"])
    for token in feeds:
        """
        Merges
        timestamp	                weth
    0	2020-12-07 13:34:34+00:00	596.193787
    1	2020-12-07 14:53:23+00:00	593.807203
    2	2020-12-07 15:29:26+00:00	595.511906
        with
        timestamp	                dai
    0	2020-12-07 14:14:03+00:00	1.003765
    1	2020-12-07 14:34:08+00:00	1.003765
    2	2020-12-07 15:11:27+00:00	1.006016
        along the timestamp column, using the previous values to fill in if the incoming df is missing that particular timestamp.

        Some columns in the final merged df may have NaNs at the top since there were no previous values to fill in from.
        """
        df = pd.merge_ordered(df, dataframeize(feeds[token], token), fill_method="ffill")
    return df

def round_dataframe_timestamp(df):
    df.timestamp = df.timestamp.round("1h")
    df = df.drop_duplicates(subset=["timestamp"]) # after rounding, some duplicates might exist
    return df

def turn_row_into_price_action(row: pd.Series, fiat_currency: str) -> typing.Dict:
    price_action = {
        "timestamp": row.timestamp.isoformat(),
        "fiat_currency": fiat_currency,
        "action": {
            "type": "external_price_update",
            "tokens": row.drop("timestamp").to_dict()
        }
    }
    return price_action
