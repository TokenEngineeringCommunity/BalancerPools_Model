import unittest
from decimal import Decimal

from model.models import Token
from model.parts.pool_method_entities import SwapExactAmountInInput, TokenAmount, SwapExactAmountInOutput, JoinParamsInput, JoinParamsOutput, \
    JoinSwapExternAmountInInput, JoinSwapExternAmountInOutput, ExitSwapPoolAmountInInput, ExitSwapPoolAmountInOutput, ExitPoolInput, ExitPoolOutput, \
    PoolMethodParamsDecoder
from model.parts.system_policies import p_swap_plot_output, p_join_pool_plot_output, p_join_swap_plot_output, p_exit_swap_plot_output, \
    p_exit_pool_plot_output, p_swap_exact_amount_in, p_join_pool, p_join_swap_extern_amount_in, p_swap_exact_amount_out, p_exit_swap_pool_amount_in, \
    p_exit_pool


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


class TestSystemPolicies(unittest.TestCase):

    def test_p_swap_exact_amount_in(self):
        initial_weth_balance = Decimal('67738.636173102396002749')
        initial_dai_balance = Decimal('10000000')
        pool = {
            'tokens': {
                'WETH': Token(bound=True, weight=Decimal('80'), denorm_weight=Decimal('40'), balance=initial_weth_balance),
                'DAI': Token(bound=True, weight=Decimal('20'), denorm_weight=Decimal('10'), balance=initial_dai_balance),
            },
            'generated_fees': {
                'WETH': Decimal('0'),
                'DAI': Decimal('0')
            },
            'pool_shares': Decimal('100'),
            'swap_fee': Decimal('0.0025')
        }
        initial_pool = pool.copy()
        current_state = {
            'pool': pool
        }
        action = {'type': 'swap',
                  'token_in': {'amount': '11861.328308360999600128', 'symbol': 'DAI'},
                  'token_out': {'amount': '20.021734699893455844', 'symbol': 'WETH'}}

        input_params, output_params = PoolMethodParamsDecoder.swap_exact_amount_in_simplified(action)
        answer = p_swap_exact_amount_in(params={}, step=1, history={}, current_state=current_state, input_params=input_params,
                                        output_params=output_params)
        self.assertAlmostEqual(answer['tokens']['DAI'].balance, initial_dai_balance + Decimal('11861.328308360999600128'))
        self.assertAlmostEqual(answer['tokens']['WETH'].balance, initial_weth_balance - Decimal('20.021734699893455844'))

    def test_p_swap_exact_amount_out_contract_call(self):
        initial_weth_balance = Decimal('67687.60745275310726724040775')
        initial_dai_balance = Decimal('10030265.38142873603805481872')
        pool = {
            'tokens': {
                'WETH': Token(bound=True, weight=Decimal('80'), denorm_weight=Decimal('40'), balance=initial_weth_balance),
                'DAI': Token(bound=True, weight=Decimal('20'), denorm_weight=Decimal('10'), balance=initial_dai_balance),
            },
            'generated_fees': {
                'WETH': Decimal('0'),
                'DAI': Decimal('0')
            },
            'pool_shares': Decimal('100'),
            'swap_fee': Decimal('0.0025')
        }
        initial_pool = pool.copy()
        current_state = {
            'pool': pool
        }
        action = {'type': 'swap', 'token_in': {'amount': '3.535578706148314394', 'symbol': 'WETH'},
                  'token_out': {'amount': '2090.162720553097945277', 'symbol': 'DAI'}}
        contract_call = {'type': 'swapExactAmountOut', 'inputs': {'tokenIn_symbol': 'WETH', 'tokenIn': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
                                                                  'maxAmountIn': '115792089237316195423570985008687907853269984665640564039457.584007913129639935',
                                                                  'tokenOut_symbol': 'DAI', 'tokenOut': '0x6B175474E89094C44Da98b954EedeAC495271d0F',
                                                                  'tokenAmountOut': '2090.162720553097945277',
                                                                  'maxPrice': '115792089237316195423570985008687907853269984665640564039457.584007913129639935'}}

        input_params, output_params = PoolMethodParamsDecoder.swap_exact_amount_out_contract_call(action, contract_call)
        answer = p_swap_exact_amount_out(params={}, step=1, history={}, current_state=current_state, input_params=input_params,
                                         output_params=output_params)
        self.assertAlmostEqual(answer['tokens']['DAI'].balance, initial_dai_balance - Decimal('2090.162720553097945277'))
        self.assertAlmostEqual(answer['tokens']['WETH'].balance, initial_weth_balance + Decimal('3.535578706148314394'))

    def test_p_join_swap_extern_amount_in(self):
        initial_weth_balance = Decimal('67958.94737692815116931411425')
        initial_dai_balance = Decimal('9872549.777138279249980148442')
        pool = {
            'tokens': {
                'WETH': Token(bound=True, weight=Decimal('0.1'), denorm_weight=Decimal('40'), balance=initial_weth_balance),
                'DAI': Token(bound=True, weight=Decimal('0.4'), denorm_weight=Decimal('10'), balance=initial_dai_balance),
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

        input_params, output_params = PoolMethodParamsDecoder.join_swap_extern_amount_in_simplified(action)
        print(input_params)
        print(output_params)
        answer = p_join_swap_extern_amount_in(params={}, step=1, history={}, current_state=current_state, input_params=input_params,
                                              output_params=output_params)
        self.assertAlmostEqual(answer['tokens']['WETH'].balance, initial_weth_balance + Decimal('26.741601415598676064'))
        self.assertAlmostEqual(answer['pool_shares'], Decimal('100') + Decimal('0.0314627351852568'))

    def test_p_join_swap_extern_amount_in_contract_call(self):
        initial_weth_balance = Decimal('67958.94737692815116931411425')
        initial_dai_balance = Decimal('9872549.777138279249980148442')
        pool = {
            'tokens': {
                'WETH': Token(bound=True, weight=Decimal('0.1'), denorm_weight=Decimal('40'), balance=initial_weth_balance),
                'DAI': Token(bound=True, weight=Decimal('0.4'), denorm_weight=Decimal('10'), balance=initial_dai_balance),
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
        contract_call = {'type': 'joinswapExternAmountIn',
                         'inputs': {'tokenIn_symbol': 'WETH', 'tokenIn': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
                                    'tokenAmountIn': '26.741601415598676064',
                                    'minPoolAmountOut': '0.031148107833404232'}}

        input_params, output_params = PoolMethodParamsDecoder.join_swap_extern_amount_in_contract_call(action, contract_call)
        print(input_params)
        print(output_params)
        answer = p_join_swap_extern_amount_in(params={}, step=1, history={}, current_state=current_state, input_params=input_params,
                                              output_params=output_params)
        self.assertAlmostEqual(answer['tokens']['WETH'].balance, initial_weth_balance + Decimal('26.741601415598676064'))
        self.assertAlmostEqual(answer['pool_shares'], Decimal('100') + Decimal('0.0314627351852568'))

    def test_p_join_pool_simplified(self):
        initial_weth_balance = Decimal('67754.45880861386396117576576')
        initial_dai_balance = Decimal('10016378.43379686305875979834')
        initial_pool_shares = Decimal('100.0035090123482194137033160')
        pool = {
            'tokens': {
                'WETH': Token(bound=True, weight=Decimal('0.1'), denorm_weight=Decimal('40'), balance=initial_weth_balance),
                'DAI': Token(bound=True, weight=Decimal('0.4'), denorm_weight=Decimal('10'), balance=initial_dai_balance),
            },
            'generated_fees': {
                'WETH': Decimal('0'),
                'DAI': Decimal('0')
            },
            'pool_shares': initial_pool_shares,
            'swap_fee': Decimal('0.0025')
        }
        current_state = {
            'pool': pool
        }
        action = {'pool_amount_out': '0.000029508254125206', 'type': 'join',
                  'tokens_in': [{'amount': '0.019993601301505542', 'symbol': 'WETH'}, {'amount': '2.954876765664920082', 'symbol': 'DAI'}]}
        contract_call = {'type': 'joinPool', 'inputs': {'poolAmountOut': '0.000029508254125206', 'maxAmountsIn': None}}

        input_params, output_params = PoolMethodParamsDecoder.join_pool_simplified(action)
        answer = p_join_pool(params={}, step=1, history={}, current_state=current_state, input_params=input_params,
                             output_params=output_params)
        self.assertAlmostEqual(answer['tokens']['WETH'].balance, initial_weth_balance + Decimal('0.019993601301505542'), 5)
        self.assertAlmostEqual(answer['tokens']['DAI'].balance, initial_dai_balance + Decimal('2.954876765664920082'), 2)
        self.assertAlmostEqual(answer['pool_shares'], initial_pool_shares + Decimal('0.000029508254125206'), 5)

    def test_p_join_pool_simplified_contract_call(self):
        initial_weth_balance = Decimal('67754.45880861386396117576576')
        initial_dai_balance = Decimal('10016378.43379686305875979834')
        initial_pool_shares = Decimal('100.0035090123482194137033160')
        pool = {
            'tokens': {
                'WETH': Token(bound=True, weight=Decimal('0.1'), denorm_weight=Decimal('40'), balance=initial_weth_balance),
                'DAI': Token(bound=True, weight=Decimal('0.4'), denorm_weight=Decimal('10'), balance=initial_dai_balance),
            },
            'generated_fees': {
                'WETH': Decimal('0'),
                'DAI': Decimal('0')
            },
            'pool_shares': initial_pool_shares,
            'swap_fee': Decimal('0.0025')
        }
        current_state = {
            'pool': pool
        }
        action = {'pool_amount_out': '0.000029508254125206', 'type': 'join',
                  'tokens_in': [{'amount': '0.019993601301505542', 'symbol': 'WETH'}, {'amount': '2.954876765664920082', 'symbol': 'DAI'}]}
        contract_call = {'type': 'joinPool', 'inputs': {'poolAmountOut': '0.000029508254125206', 'maxAmountsIn': None}}

        input_params, output_params = PoolMethodParamsDecoder.join_pool_contract_call(action, contract_call)
        answer = p_join_pool(params={}, step=1, history={}, current_state=current_state, input_params=input_params,
                             output_params=output_params)
        self.assertAlmostEqual(answer['tokens']['WETH'].balance, initial_weth_balance + Decimal('0.019993601301505542'), 5)
        self.assertAlmostEqual(answer['tokens']['DAI'].balance, initial_dai_balance + Decimal('2.954876765664920082'), 2)
        self.assertAlmostEqual(answer['pool_shares'], initial_pool_shares + Decimal('0.000029508254125206'), 5)

    def test_p_exit_swap_pool_amount_in_simplified(self):
        initial_weth_balance = Decimal('68804.59546436957187327149066')
        initial_dai_balance = Decimal('9415058.959645000758262408416')
        initial_pool_shares = Decimal('100.0314627351852321785331753')
        pool = {
            'tokens': {
                'WETH': Token(bound=True, weight=Decimal('0.1'), denorm_weight=Decimal('40'), balance=initial_weth_balance),
                'DAI': Token(bound=True, weight=Decimal('0.4'), denorm_weight=Decimal('10'), balance=initial_dai_balance),
            },
            'generated_fees': {
                'WETH': Decimal('0'),
                'DAI': Decimal('0')
            },
            'pool_shares': initial_pool_shares,
            'swap_fee': Decimal('0.0025')
        }
        current_state = {
            'pool': pool
        }
        action = {'pool_amount_in': '0.0314627351852568', 'type': 'exit_swap', 'token_out': {'amount': '27.036668416618733348', 'symbol': 'WETH'}}
        input_params, output_params = PoolMethodParamsDecoder.exit_swap_pool_amount_in_simplified(action)
        answer = p_exit_swap_pool_amount_in(params={}, step=1, history={}, current_state=current_state, input_params=input_params,
                                            output_params=output_params)
        self.assertAlmostEqual(answer['tokens']['WETH'].balance, initial_weth_balance - Decimal('27.036668416618733348'), 4)
        self.assertAlmostEqual(answer['pool_shares'], initial_pool_shares - Decimal('0.0314627351852568'))

    def test_p_exit_swap_pool_amount_in_contract_call(self):
        initial_weth_balance = Decimal('68804.59546436957187327149066')
        initial_dai_balance = Decimal('9415058.959645000758262408416')
        initial_pool_shares = Decimal('100.0314627351852321785331753')
        pool = {
            'tokens': {
                'WETH': Token(bound=True, weight=Decimal('0.1'), denorm_weight=Decimal('40'), balance=initial_weth_balance),
                'DAI': Token(bound=True, weight=Decimal('0.4'), denorm_weight=Decimal('10'), balance=initial_dai_balance),
            },
            'generated_fees': {
                'WETH': Decimal('0'),
                'DAI': Decimal('0')
            },
            'pool_shares': initial_pool_shares,
            'swap_fee': Decimal('0.0025')
        }
        current_state = {
            'pool': pool
        }
        action = {'pool_amount_in': '0.0314627351852568', 'type': 'exit_swap', 'token_out': {'amount': '27.036668416618733348', 'symbol': 'WETH'}}
        contract_call = {'type': 'exitswapPoolAmountIn',
                         'inputs': {'tokenOut_symbol': 'WETH', 'tokenOut': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
                                    'poolAmountIn': '0.0314627351852568',
                                    'minAmountOut': '26.76630173245254765'}}

        input_params, output_params = PoolMethodParamsDecoder.exit_swap_pool_amount_in_contract_call(action, contract_call)
        answer = p_exit_swap_pool_amount_in(params={}, step=1, history={}, current_state=current_state, input_params=input_params,
                                            output_params=output_params)
        self.assertAlmostEqual(answer['tokens']['WETH'].balance, initial_weth_balance - Decimal('27.036668416618733348'), 4)
        self.assertAlmostEqual(answer['pool_shares'], initial_pool_shares - Decimal('0.0314627351852568'))

    def test_p_exit_pool_simpl(self):
        initial_weth_balance = Decimal('67180.99053842917941285506345')
        initial_dai_balance = Decimal('10439411.60763212320360230771')
        initial_pool_shares = Decimal('100.0103783872866677807449608')
        pool = {
            'tokens': {
                'WETH': Token(bound=True, weight=Decimal('0.1'), denorm_weight=Decimal('40'), balance=initial_weth_balance),
                'DAI': Token(bound=True, weight=Decimal('0.4'), denorm_weight=Decimal('10'), balance=initial_dai_balance),
            },
            'generated_fees': {
                'WETH': Decimal('0'),
                'DAI': Decimal('0')
            },
            'pool_shares': initial_pool_shares,
            'swap_fee': Decimal('0.0025')
        }
        current_state = {
            'pool': pool
        }
        action = {'pool_amount_in': '0.001191587214967108', 'type': 'exit',
                  'tokens_out': [{'amount': '0.800443097642618074', 'symbol': 'WETH'}, {'amount': '124.378005824396584765', 'symbol': 'DAI'}]}

        input_params, output_params = PoolMethodParamsDecoder.exit_pool_simplified(action)
        answer = p_exit_pool(params={}, step=1, history={}, current_state=current_state, input_params=input_params,
                                            output_params=output_params)
        self.assertAlmostEqual(answer['tokens']['WETH'].balance, initial_weth_balance - Decimal('0.800443097642618074'), 4)
        self.assertAlmostEqual(answer['tokens']['DAI'].balance, initial_dai_balance - Decimal('124.378005824396584765'), 2)
        self.assertAlmostEqual(answer['pool_shares'], initial_pool_shares - Decimal('0.001191587214967108'))

    def test_p_exit_pool_contract_call(self):
        initial_weth_balance = Decimal('67180.99053842917941285506345')
        initial_dai_balance = Decimal('10439411.60763212320360230771')
        initial_pool_shares = Decimal('100.0103783872866677807449608')
        pool = {
            'tokens': {
                'WETH': Token(bound=True, weight=Decimal('0.1'), denorm_weight=Decimal('40'), balance=initial_weth_balance),
                'DAI': Token(bound=True, weight=Decimal('0.4'), denorm_weight=Decimal('10'), balance=initial_dai_balance),
            },
            'generated_fees': {
                'WETH': Decimal('0'),
                'DAI': Decimal('0')
            },
            'pool_shares': initial_pool_shares,
            'swap_fee': Decimal('0.0025')
        }
        current_state = {
            'pool': pool
        }
        action = {'pool_amount_in': '0.001191587214967108', 'type': 'exit',
                  'tokens_out': [{'amount': '0.800443097642618074', 'symbol': 'WETH'}, {'amount': '124.378005824396584765', 'symbol': 'DAI'}]}
        contract_call = {'type': 'exitPool', 'inputs': {'poolAmountIn': '0.001191587214967108', 'minAmountsOut': None}}

        input_params, output_params = PoolMethodParamsDecoder.exit_pool_contract_call(action, contract_call)
        answer = p_exit_pool(params={}, step=1, history={}, current_state=current_state, input_params=input_params,
                                            output_params=output_params)
        self.assertAlmostEqual(answer['tokens']['WETH'].balance, initial_weth_balance - Decimal('0.800443097642618074'), 4)
        self.assertAlmostEqual(answer['tokens']['DAI'].balance, initial_dai_balance - Decimal('124.378005824396584765'), 2)
        self.assertAlmostEqual(answer['pool_shares'], initial_pool_shares - Decimal('0.001191587214967108'))

if __name__ == '__main__':
    unittest.main()
