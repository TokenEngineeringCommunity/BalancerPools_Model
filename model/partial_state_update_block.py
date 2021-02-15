from model.parts.system_policies import ActionDecoder
from model.parts.general_state_updates import s_update_change_datetime, s_update_action_type
from model.parts.pool_state_updates import s_update_pool, s_update_spot_prices
from model.parts.external_price_feed_state_updates import s_update_external_price_feeds


def generate_partial_state_update_blocks(path_to_action_json: str) -> dict:
    steps_number = ActionDecoder.load_actions(path_to_action_json)
    return {
        'partial_state_update_blocks': [
            {
                # system_policies.py
                'policies': {
                    'user_action': ActionDecoder.p_action_decoder,
                },
                'variables': {
                    'pool': s_update_pool,
                    'change_datetime': s_update_change_datetime,
                    'token_prices': s_update_external_price_feeds,
                    'action_type': s_update_action_type,
                    'spot_prices': s_update_spot_prices
                }
            },

        ],
        'steps_number': steps_number,
    }
