import typing
from decimal import Decimal, getcontext
# import ipdb
from enum import Enum

import pandas as pd
from attr import dataclass

from model.parts.balancer_math import BalancerMath
from model.parts.pool_method_entities import PoolMethodParamsDecoder
from model.parts.utils import get_param
import pandas as pd

getcontext().prec = 28


class ActionDecodingType(Enum):
    simplified = "SIMPLIFIED"
    contract_call = "CONTRACT_CALL"
    replay_output = "REPLAY_OUTPUT"


class ActionDecoder:
    action_df = None
    decoding_type = ActionDecodingType.simplified

    @classmethod
    def load_actions(cls, path_to_action_file: str, only_prices=False) -> int:
        ActionDecoder.action_df = pd.read_json(path_to_action_file).drop(0)

        return len(ActionDecoder.action_df)

    @staticmethod
    def p_simplified_action_decoder(idx, params, step, history, current_state):
        action = ActionDecoder.action_df['action'][idx]
        timestamp = ActionDecoder.action_df['timestamp'][idx]
        if action['type'] == 'swap':
            pool_method_params = PoolMethodParamsDecoder.swap_exact_amount_in_simplified(action)
        elif action['type'] == 'join':
            pool_method_params = PoolMethodParamsDecoder.join_pool_simplified(action)
        elif action['type'] == 'join_swap':
            pool_method_params = PoolMethodParamsDecoder.join_swap_extern_amount_in_simplified(action)
        elif action['type'] == 'exit_swap':
            pool_method_params = PoolMethodParamsDecoder.exit_swap_pool_amount_in_simplified(action)
        elif action['type'] == 'exit':
            pool_method_params = PoolMethodParamsDecoder.exit_pool_simplified(action)
        elif action['type'] == 'external_price_update':
            return {'external_price_update': action['tokens'], 'change_datetime_update': timestamp, 'action_type': action['type'],
                    # 'pool_update': None
                    }
        else:
            raise Exception("Action type {} unimplemented".format(action['type']))
        return {'pool_update': pool_method_params, 'change_datetime_update': timestamp, 'action_type': action['type']}

    @staticmethod
    def p_contract_call_action_decoder(idx, params, step, history, current_state):
        action = ActionDecoder.action_df['action'][idx]
        timestamp = ActionDecoder.action_df['timestamp'][idx]
        contract_call = None
        if action['type'] != 'external_price_update':
            contract_call = ActionDecoder.action_df['contract_call'][idx][0]
        else:
            return {'external_price_update': action['tokens'], 'change_datetime_update': timestamp, 'action_type': action['type'],
                    # 'pool_update': None
                    }
        if contract_call['type'] == 'joinswapExternAmountIn':
            pool_method_params = PoolMethodParamsDecoder.join_swap_extern_amount_in_contract_call(action, contract_call)
        elif contract_call['type'] == 'joinPool':
            pool_method_params = PoolMethodParamsDecoder.join_pool_contract_call(action, contract_call)
        elif contract_call['type'] == 'swapExactAmountIn':
            pool_method_params = PoolMethodParamsDecoder.swap_exact_amount_in_contract_call(action, contract_call)
        elif contract_call['type'] == 'swapExactAmountOut':
            pool_method_params = PoolMethodParamsDecoder.swap_exact_amount_out_contract_call(action, contract_call)
        elif contract_call['type'] == 'exitPool':
            pool_method_params = PoolMethodParamsDecoder.exit_pool_contract_call(action, contract_call)
        elif contract_call['type'] == 'exitswapPoolAmountIn':
            pool_method_params = PoolMethodParamsDecoder.exit_swap_pool_amount_in_contract_call(action, contract_call)
        elif contract_call['type'] == 'exitswapExternAmountOut':
            pool_method_params = PoolMethodParamsDecoder.exit_swap_extern_amount_out_contract_call(action, contract_call)
        else:
            raise Exception("Action type {} unimplemented".format(action['type']))
        return {'pool_update': pool_method_params, 'change_datetime_update': timestamp, 'action_type': action['type']}

    @staticmethod
    def p_plot_output_action_decoder(idx, params, step, history, current_state):
        action = ActionDecoder.action_df['action'][idx]
        timestamp = ActionDecoder.action_df['timestamp'][idx]
        if action['type'] == 'swap':
            pool_method_params = PoolMethodParamsDecoder.swap_exact_amount_in_simplified(action)
        elif action['type'] == 'join':
            pool_method_params = PoolMethodParamsDecoder.join_pool_simplified(action)
        elif action['type'] == 'join_swap':
            pool_method_params = PoolMethodParamsDecoder.join_swap_extern_amount_in_simplified(action)
        elif action['type'] == 'exit_swap':
            pool_method_params = PoolMethodParamsDecoder.exit_swap_pool_amount_in_simplified(action)
        elif action['type'] == 'exit':
            pool_method_params = PoolMethodParamsDecoder.exit_pool_simplified(action)
        elif action['type'] == 'external_price_update':
            return {'external_price_update': action['tokens'], 'change_datetime_update': timestamp, 'action_type': action['type'],
                    'pool_update': None}
        else:
            raise Exception("Action type {} unimplemented".format(action['type']))
        return {'pool_update': pool_method_params, 'change_datetime_update': timestamp, 'action_type': action['type']}

    @staticmethod
    def p_action_decoder(params, step, history, current_state):
        if ActionDecoder.action_df is None:
            raise Exception('call ActionDecoder.load_actions(path_to_action.json) first')
        '''
        In this simplified model of Balancer, we have not modeled user behavior. Instead, we map events to actions.
        '''
        decoding_type = get_param(params, 'decoding_type')

        ActionDecoder.decoding_type = ActionDecodingType(decoding_type)
        idx = current_state['timestep'] + 1
        if ActionDecoder.decoding_type == ActionDecodingType.simplified:
            return ActionDecoder.p_simplified_action_decoder(idx, params, step, history, current_state)
        elif ActionDecoder.decoding_type == ActionDecodingType.contract_call:
            return ActionDecoder.p_contract_call_action_decoder(idx, params, step, history, current_state)
        elif ActionDecoder.decoding_type == ActionDecodingType.replay_output:
            return ActionDecoder.p_plot_output_action_decoder(idx, params, step, history, current_state)
        else:
            raise Exception(f'unknown decoding type {decoding_type}')
