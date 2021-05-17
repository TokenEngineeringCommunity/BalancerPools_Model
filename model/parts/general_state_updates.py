from model.parts.pool_method_entities import TokenAmount
from model.parts.utils import get_param

def s_update_change_datetime(params, substep, state_history, previous_state, policy_input):
    change_datetime = policy_input.get('change_datetime_update')
    if change_datetime is None:
        return 'change_datetime', ''
    return 'change_datetime', change_datetime

def s_update_action_type(params, substep, state_history, previous_state, policy_input):
    action_type = policy_input.get('action_type')
    if action_type is None:
        return 'action_type', ''
    return 'action_type', action_type

def s_record_arbitrageur_trade(params, substep, state_history, previous_state, policy_input):
    arb_trade = policy_input.get('arbitrageur_trade')
    if arb_trade is None:
        return 'arbitrageur_trade', None
    return 'arbitrageur_trade', arb_trade
