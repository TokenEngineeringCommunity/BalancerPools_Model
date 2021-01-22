from model.parts.system_policies import p_action_decoder, p_external_price_feed_decoder
from model.parts.pool_state_updates import s_update_pool
from model.parts.external_price_feed_state_updates import s_update_external_price_feeds

partial_state_update_block = [
    {
        # system_policies.py
        'policies': {
            'user_action': p_action_decoder,
            'external_price_feeds': p_external_price_feed_decoder
        },
        'variables': {
            'pool': s_update_pool,
            'token_values': s_update_external_price_feeds
        }
    }
]