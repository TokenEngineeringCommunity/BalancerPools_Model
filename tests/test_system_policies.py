import unittest
from decimal import Decimal

from model.models import Token
from model.parts.pool_method_entities import SwapExactAmountInInput, TokenAmount, SwapExactAmountInOutput, JoinParamsInput, JoinParamsOutput, \
    JoinSwapExternAmountInInput, JoinSwapExternAmountInOutput, ExitSwapPoolAmountInInput, ExitSwapPoolAmountInOutput, ExitPoolInput, ExitPoolOutput, \
    PoolMethodParamsDecoder
from model.parts.system_policies import p_swap_plot_output, p_join_pool_plot_output, p_join_swap_plot_output, p_exit_swap_plot_output, \
    p_exit_pool_plot_output, p_swap_exact_amount_in, p_join_pool


class TestPlotOutputSystemPolicies(unittest.TestCase):

    def test_p_swap_plot_output(self):
        pool = {
            'tokens': {
                'WETH': Token(bound=True, weight=Decimal('50'), denorm_weight=Decimal('20'), balance=Decimal('100.0')),
                'DAI': Token(bound=True, weight=Decimal('50'), denorm_weight=Decimal('20'), balance=Decimal('100.0')),
            }
        }
        current_state = {
            'pool': pool
        }

        input_params = SwapExactAmountInInput(token_in=TokenAmount.ta_with_dict({
            "amount": "110334.994151207114657145",
            "symbol": "DAI"
        }), min_token_out=TokenAmount.ta_with_dict({
            "amount": "94.18699055387891619",
            "symbol": "WETH"
        }))
        output_params = SwapExactAmountInOutput(token_out=TokenAmount.ta_with_dict({
            "amount": "94.18699055387891619",
            "symbol": "WETH"
        }))
        result_pool = p_swap_plot_output(params={}, step=1, history={}, current_state=current_state, input_params=input_params,
                                         output_params=output_params)
        self.assertAlmostEqual(result_pool['tokens']['WETH'].balance, Decimal('100') - Decimal('94.18699055387891619'))
        self.assertAlmostEqual(result_pool['tokens']['DAI'].balance, Decimal('100') + Decimal('110334.994151207114657145'))

    def test_p_join_pool_plot_output(self):
        pool = {
            'tokens': {
                'WETH': Token(bound=True, weight=Decimal('50'), denorm_weight=Decimal('20'), balance=Decimal('100.0')),
                'DAI': Token(bound=True, weight=Decimal('50'), denorm_weight=Decimal('20'), balance=Decimal('100.0')),
            },
            'pool_shares': Decimal('10')
        }
        current_state = {
            'pool': pool
        }
        input_params = JoinParamsInput(pool_amount_out=Decimal('0.003553700696304231'), tokens_in=['WETH, DAI'])
        output_params = JoinParamsOutput(tokens_in=[
            TokenAmount.ta_with_dict({
                "amount": "2.149934784657617805",
                "symbol": "WETH"
            }),
            TokenAmount.ta_with_dict({
                "amount": "582.4545134357713927",
                "symbol": "DAI"
            })
        ])
        result_pool = p_join_pool_plot_output(params={}, step=1, history={}, current_state=current_state, input_params=input_params,
                                              output_params=output_params)
        self.assertAlmostEqual(result_pool['tokens']['WETH'].balance, Decimal('100') + Decimal('2.149934784657617805'))
        self.assertAlmostEqual(result_pool['tokens']['DAI'].balance, Decimal('100') + Decimal('582.4545134357713927'))
        self.assertAlmostEqual(result_pool['pool_shares'], Decimal('10') + Decimal('0.003553700696304231'))

    def test_p_join_swap_plot_output(self):
        pool = {
            'tokens': {
                'WETH': Token(bound=True, weight=Decimal('50'), denorm_weight=Decimal('20'), balance=Decimal('100.0')),
                'DAI': Token(bound=True, weight=Decimal('50'), denorm_weight=Decimal('20'), balance=Decimal('100.0')),
            },
            'pool_shares': Decimal('10')
        }
        current_state = {
            'pool': pool
        }

        input_params = JoinSwapExternAmountInInput(token_in=TokenAmount.ta_with_dict({
            "amount": "15377.818885119467224322",
            "symbol": "DAI"
        }))
        output_params = JoinSwapExternAmountInOutput(pool_amount_out=Decimal('0.017357248617768192'))
        result_pool = p_join_swap_plot_output(params={}, step=1, history={}, current_state=current_state, input_params=input_params,
                                              output_params=output_params)
        self.assertAlmostEqual(result_pool['tokens']['DAI'].balance, Decimal('100') + Decimal('15377.818885119467224322'))
        self.assertAlmostEqual(result_pool['pool_shares'], Decimal('10') + Decimal('0.017357248617768192'))

    def test_p_exit_swap_plot_output(self):
        pool = {
            'tokens': {
                'WETH': Token(bound=True, weight=Decimal('50'), denorm_weight=Decimal('20'), balance=Decimal('100.0')),
                'DAI': Token(bound=True, weight=Decimal('50'), denorm_weight=Decimal('20'), balance=Decimal('100.0')),
            },
            'pool_shares': Decimal('10')
        }
        current_state = {
            'pool': pool
        }

        input_params = ExitSwapPoolAmountInInput(pool_amount_in=Decimal('0.001425953068795668'))
        output_params = ExitSwapPoolAmountInOutput(token_out=TokenAmount.ta_with_dict({
            "amount": "1.053713331470558907",
            "symbol": "WETH"
        }))
        result_pool = p_exit_swap_plot_output(params={}, step=1, history={}, current_state=current_state, input_params=input_params,
                                              output_params=output_params)
        self.assertAlmostEqual(result_pool['tokens']['WETH'].balance, Decimal('100') - Decimal('1.053713331470558907'))
        self.assertAlmostEqual(result_pool['pool_shares'], Decimal('10') - Decimal('0.001425953068795668'))

    def test_p_exit_pool_plot_output(self):
        pool = {
            'tokens': {
                'WETH': Token(bound=True, weight=Decimal('50'), denorm_weight=Decimal('20'), balance=Decimal('100.0')),
                'DAI': Token(bound=True, weight=Decimal('50'), denorm_weight=Decimal('20'), balance=Decimal('100.0')),
            },
            'pool_shares': Decimal('10')
        }
        current_state = {
            'pool': pool
        }
        input_params = ExitPoolInput(pool_amount_in=Decimal('0.084785200842684343'))
        output_params = ExitPoolOutput(tokens_out=[
            TokenAmount.ta_with_dict({
                "amount": "49.947987341742463214",
                "symbol": "WETH"
            }),
            TokenAmount.ta_with_dict({
                "amount": "15583.368940028059875724",
                "symbol": "DAI"
            })
        ])
        result_pool = p_exit_pool_plot_output(params={}, step=1, history={}, current_state=current_state, input_params=input_params,
                                              output_params=output_params)
        self.assertAlmostEqual(result_pool['tokens']['WETH'].balance, Decimal('100') - Decimal('49.947987341742463214'))
        self.assertAlmostEqual(result_pool['tokens']['DAI'].balance, Decimal('100') - Decimal('15583.368940028059875724'))
        self.assertAlmostEqual(result_pool['pool_shares'], Decimal('10') - Decimal('0.084785200842684343'))

class TestSimplifiedSystemPolicies(unittest.TestCase):

    def test_p_swap_exact_amount_in(self):
        pool = {
            'tokens': {
                'WETH': Token(bound=True, weight=Decimal('0.1'), denorm_weight=Decimal('10'), balance=Decimal('67738.636173102396002749')),
                'DAI': Token(bound=True, weight=Decimal('0.4'), denorm_weight=Decimal('40'), balance=Decimal('10000000')),
            },
            'generated_fees': {
                'WETH': Decimal('0'),
                'DAI': Decimal('0')
            },
            'pool_shares': Decimal('100'),
            'swap_fee': Decimal('0.0025')
        }
        current_state = {
            'pool': pool
        }
        action = {'type': 'swap',
                  'token_in': {'amount': '11861.328308360999600128', 'symbol': 'DAI'},
                  'token_out': {'amount': '20.021734699893455844', 'symbol': 'WETH'}}

        input_params, output_params = PoolMethodParamsDecoder.swap_exact_amount_in_simplified(action)
        answer = p_swap_exact_amount_in(params={}, step=1, history={}, current_state=current_state, input_params=input_params, output_params=output_params)
        self.assertAlmostEqual(pool['tokens']['DAI'].balance, pool['tokens']['DAI'].balance+Decimal('11861.328308360999600128'))
        self.assertAlmostEqual(pool['tokens']['WETH'].balance, pool['tokens']['WETH'].balance-Decimal('20.021734699893455844'))

    @unittest.skip(reason='TODO')
    def test_p_join_swap_extern_amount_in(self):

        pool = {
            'tokens': {
                'WETH': Token(bound=True, weight=Decimal('0.1'), denorm_weight=Decimal('10'), balance=Decimal('9872549.777138279249980148442')),
                'DAI': Token(bound=True, weight=Decimal('0.4'), denorm_weight=Decimal('40'), balance=Decimal('67958.94737692815116931411425')),
            },
            'generated_fees': {
                'WETH': Decimal('0'),
                'DAI': Decimal('0')
            },
            'pool_shares': Decimal('100'),
            'swap_fee': Decimal('0.0025')
        }
        current_state = {
            'pool': pool
        }
        action = {'pool_amount_out': '0.0314627351852568', 'type': 'join_swap', 'token_in': {'amount': '26.741601415598676064', 'symbol': 'WETH'}}

        input_params, output_params = PoolMethodParamsDecoder.swap_exact_amount_in_simplified(action)
        answer = p_swap_exact_amount_in(params={}, step=1, history={}, current_state=current_state, input_params=input_params, output_params=output_params)
        self.assertAlmostEqual(pool['tokens']['WETH'].balance, pool['tokens']['WETH'].balance+Decimal('26.741601415598676064'))
        self.assertAlmostEqual(pool['pool_shares'], Decimal('100') * Decimal('0.0314627351852568'))
    '''
    def test_p_join_pool(self):
        input_params, output_params = PoolMethodParamsDecoder.join_pool_simplified(action)
        answer = p_join_pool(params, step, history, current_state, input_params, output_params)
    
    def test_p_join_swap_extern_amount_in(self):
        input_params, output_params = PoolMethodParamsDecoder.join_swap_extern_amount_in_simplified(action)
        answer = p_join_swap_extern_amount_in(params, step, history, current_state, input_params, output_params)
        
    def test_p_exit_swap_pool_amount_in(self):
        input_params, output_params = PoolMethodParamsDecoder.exit_swap_pool_amount_in_simplified(action)
        answer = p_exit_swap_pool_amount_in(params, step, history, current_state, input_params, output_params)

    def test_p_exit_pool(self):
        input_params, output_params = PoolMethodParamsDecoder.exit_pool_simplified(action)
        answer = p_exit_pool(params, step, history, current_state, input_params, output_params)
    '''

if __name__ == '__main__':
    unittest.main()
