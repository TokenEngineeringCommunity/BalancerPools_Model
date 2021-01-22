import pandas as pd

action_df = pd.read_json('model/parts/actions-WETH-DAI-0x8b6e6e7b5b3801fed2cafd4b22b8a16c2f2db21a.json')
weth_price_feed = pd.read_csv('model/parts/actions-WETH-DAI-0x8b6e6e7b5b3801fed2cafd4b22b8a16c2f2db21a.json')
dai_price_feed = pd.read_json('model/parts/actions-WETH-DAI-0x8b6e6e7b5b3801fed2cafd4b22b8a16c2f2db21a.json')


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

    
    return {'external_price_update': None}
