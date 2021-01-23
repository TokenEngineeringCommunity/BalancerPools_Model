from datetime import timedelta, timezone
from decimal import Decimal

import pandas as pd

action_df = pd.read_json('model/parts/actions-WETH-DAI-0x8b6e6e7b5b3801fed2cafd4b22b8a16c2f2db21a.json')
weth_price_feed = pd.read_csv('model/parts/COINBASE_ETHUSD_5.csv', sep=';')
dai_price_feed = pd.read_csv('model/parts/COINBASE_DAIUSD_5.csv', sep=';')
PRICE_FEED_STEP_SECONDS = 300


def p_action_decoder(params, step, history, current_state):
    '''
    In this simplified model of Balancer, we have not modeled user behavior. Instead, we map events to actions.
    '''
    prev_timestep = current_state['timestep']
    if step > 1:
        prev_timestep -= 1

    # skip the first event, as they are already accounted for in the initial conditions of the system
    data_counter = prev_timestep + 1
    tx = action_df.loc[action_df['timestep'] == data_counter]
    if tx.empty:
        return {'pool_update': None}
    else:
        return {'pool_update': tx['action']}


def p_external_price_feed_decoder(params, step, history, current_state):
    prev_timestep = current_state['timestep']
    if step > 1:
        prev_timestep -= 1

    # skip the first event, as they are already accounted for in the initial conditions of the system
    data_counter = prev_timestep + 1
    first_tx = action_df.loc[action_df['timestep'] == 0]

    first_date = pd.to_datetime(first_tx['datetime'])
    # first date + data_counter seconds = current_datetime
    current_datetime = first_date + timedelta(seconds=data_counter)
    curr_date = current_datetime[0].replace(tzinfo=timezone.utc)
    print('curr_date', curr_date)
    formatted_curr_datetime = current_datetime.iloc[0].isoformat()

    price_feeds = [{
        'token': 'DAI',
        'pricefeed': dai_price_feed
    },
        {
            'token': 'WETH',
            'pricefeed': weth_price_feed
        }
    ]
    external_price_updates = {}
    '''
        If nearest price is later than current, get also prev price, and if sooner, get also next price.
        then linear interpolation https://en.wikipedia.org/wiki/Linear_interpolation

    '''
    for item in price_feeds:
        token = item['token']
        pricefeed = item['pricefeed']
        earlier_price_row = pricefeed.query(f"time <= '{formatted_curr_datetime}'").tail(1)
        earlier_date = pd.to_datetime(earlier_price_row['time'])[0].replace(tzinfo=timezone.utc)
        earlier_close = earlier_price_row['close'][0]
        print('earlier_date', earlier_date)
        print('earlier_close', earlier_close)
        later_price_row = pricefeed.query(f"time > '{formatted_curr_datetime}'").head(1)
        later_open = later_price_row['open'][1]
        later_date = pd.to_datetime(later_price_row['time'])[1].replace(tzinfo=timezone.utc)
        print('later_open', later_open)
        print('later_date', later_date)

        price = (earlier_close * (later_date - curr_date) + later_open * (curr_date - earlier_date)) / (later_date - earlier_date)
        external_price_updates[token] = price

    return {'external_price_update': external_price_updates}
