from model.parts.arbitrage_policies import p_arbitrageur
from model.parts.system_policies import ActionDecoder
from model.parts.general_state_updates import s_update_change_datetime, s_update_action_type
from model.parts.pool_state_updates import s_update_pool, s_update_spot_prices
from model.parts.external_price_feed_state_updates import s_update_external_price_feeds


def generate_partial_state_update_blocks(path_to_action_json: str, add_arbitrage = False) -> dict:
    steps_number = ActionDecoder.load_actions(path_to_action_json)
    blocks = {
        'partial_state_update_blocks': [
            {
                'policies': {
                    'external_signals': ActionDecoder.p_action_decoder,
                },
                'variables': {
                    'pool': s_update_pool,
                    'change_datetime': s_update_change_datetime,
                    'token_prices': s_update_external_price_feeds,
                    'action_type': s_update_action_type,
                    'spot_prices': s_update_spot_prices,
                }
            },
        ],
        'steps_number': steps_number,
    }
    if add_arbitrage:
        blocks['partial_state_update_blocks'][0]['policies']['arbitrage'] = p_arbitrageur
    return blocks

