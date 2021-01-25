from datetime import timedelta, timezone, datetime
import dateutil.parser

import pandas as pd

action_df = pd.read_json('model/parts/actions-WETH-DAI-0x8b6e6e7b5b3801fed2cafd4b22b8a16c2f2db21a.json')


def p_action_decoder(params, step, history, current_state):
    '''
    In this simplified model of Balancer, we have not modeled user behavior. Instead, we map events to actions.
    '''
    prev_timestep = current_state['timestep']
    if step > 1:
        prev_timestep -= 1

    # skip the first event, as they are already accounted for in the initial conditions of the system
    data_counter = prev_timestep + 1
    action = action_df['action'][data_counter]
    return {'pool_update': action, 'change_datetime_update': action['datetime']}


