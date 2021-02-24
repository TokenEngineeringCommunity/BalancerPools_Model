import typing
from pycoingecko import CoinGeckoAPI
from datetime import datetime, timedelta, timezone
cg = CoinGeckoAPI()
symbol_id_map = {}

def initialize_coingecko_api():
    cg_coins_list = cg.get_coins_list()

    for c in cg_coins_list:
        symbol_id_map[c['symbol']] = c['id']

def tidy_up_prices(prices: typing.List[typing.List], initial_state: typing.Dict) -> typing.List[typing.Tuple]:
    """
    input [[timestamp_ms, price_avg], [..]...] (90d ago -> now, 180d ago -> 90d ago, 270d ago -> 180d ago)
    output [(datetime(timestamp_s), price_avg), (..)...] (sorted by timestamp)
    """
    p2 = [(datetime.fromtimestamp(int(p[0]/1000), timezone.utc), p[1]) for p in prices]
    p2.sort(key=lambda p: p[0])

    p3 = [(round_time(p[0]), p[1]) for p in p2]
    return only_prices_after_initial_state(p3, initial_state)

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

def round_time(dt=None, date_delta=timedelta(hours=1), to='average'):
    """
    Round a datetime object to a multiple of a timedelta
    dt : datetime.datetime object, default now.
    dateDelta : timedelta object, we round to a multiple of this, default 1 minute.
    from:  http://stackoverflow.com/questions/3463930/how-to-round-the-minute-of-a-datetime-object-python
    """
    DTMIN_UTCAWARE = datetime(1,1,1,0,0,0,0,timezone.utc)  # dt.min is not timezone aware

    round_to = date_delta.total_seconds()
    if dt is None:
        dt = datetime.now(timezone.utc)
    seconds = (dt - DTMIN_UTCAWARE).seconds

    if seconds % round_to == 0 and dt.microsecond == 0:
        rounding = (seconds + round_to / 2) // round_to * round_to
    else:
        if to == 'up':
            # // is a floor division, not a comment on following line (like in javascript):
            rounding = (seconds + dt.microsecond/1000000 + round_to) // round_to * round_to
        elif to == 'down':
            rounding = seconds // round_to * round_to
        else:
            rounding = (seconds + round_to / 2) // round_to * round_to

    return dt + timedelta(0, rounding - seconds, - dt.microsecond)

def only_prices_after_initial_state(prices: typing.List[typing.Tuple], initial_state_datetime: datetime) -> typing.List[typing.Tuple]:
    for i, p in enumerate(prices):
        if p[0] > initial_state_datetime:
            return prices[i:]
    raise Exception("There is no price data available after the simulation's starting point")

# def add_price_updates_to_actions(actions, prices, base):
