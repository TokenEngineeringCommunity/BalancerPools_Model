from model.parts.system_policies import p_action_decoder
from model.parts.pool_state_updates import s_update_pool

partial_state_update_block = [
    {
        # system_policies.py
        'policies': {
            'user_action': p_action_decoder
        },
        'variables': {
            'pool': s_update_pool,
        }
    }
]