
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
