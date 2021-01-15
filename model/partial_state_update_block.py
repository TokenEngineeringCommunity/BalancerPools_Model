from model.parts.system import p_action_decoder, su_update_pool

partial_state_update_block = [
    {
        # system.py
        'policies': {
            'user_action': p_action_decoder
        },
        'variables': {
            'pool': su_update_pool,
        }
    }
]