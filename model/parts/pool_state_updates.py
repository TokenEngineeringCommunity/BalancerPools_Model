def s_update_pool(params, substep, state_history, previous_state, policy_input):
    action = policy_input.get('pool_update')
    if action is None:
        return 'pool', previous_state['pool']
    return 'pool', action
