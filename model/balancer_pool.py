from collections import namedtuple
from decimal import Decimal, ROUND_HALF_DOWN

from model.balancer_constants import MIN_FEE, MAX_BOUND_TOKENS, INIT_POOL_SUPPLY, EXIT_FEE, MAX_IN_RATIO, MAX_OUT_RATIO
from model.balancer_math import BalancerMath
from dataclasses import dataclass


@dataclass
class TokenRecord:
    bound: bool
    name: str
    denorm: Decimal
    balance: Decimal

@dataclass
class SwapInResult:
    token_amount_out: Decimal
    spot_price_after: Decimal

@dataclass
class SwapOutResult:
    token_amount_in: Decimal
    spot_price_after: Decimal

class BalancerPool(BalancerMath):

    def __init__(self, initial_pool_supply: Decimal = INIT_POOL_SUPPLY):
        self._swap_fee = MIN_FEE
        self._records = {}  # NOTE: we are assuming python 3.6+ ordered dictionaries
        self.total_weight = Decimal('0')
        self.pool_token_supply = initial_pool_supply

    def get_total_denorm_weight(self):
        return self.total_weight

    def get_denorm_weight(self, token: str):
        return self._records[token].denorm

    def get_normal_weight(self, token: str):
        denorm = self._records[token].denorm
        return denorm / self.total_weight

    def get_balance(self, token: str):
        return self._records[token].balance

    def get_num_tokens(self):
        return len(self._records)

    def _mint_pool_share(self, amount: Decimal):
        self.pool_token_supply += amount

    def _burn_pool_share(self, amount: Decimal):
        self.pool_token_supply -= amount

    def set_swap_fee(self, amount: Decimal):
        self._swap_fee = amount

    def bind(self, token: str, balance: Decimal, denorm: int):

        if self._records.get(token) is not None and self._records.get(token).bound is True:
            raise Exception('ERR_ALREADY_BOUND')
        # TODO limit number of tokens to MAX_BOUND_TOKENS
        self._records[token] = TokenRecord(True, token, 0, 0)
        self.rebind(token, balance, denorm)

    def rebind(self, token: str, balance: Decimal, denorm: int):
        if not self._records[token].bound:
            raise Exception("ERR_NOT_BOUND")
        # TODO if self._finalized:
        #    raise Exception("ERR_IS_FINALIZED")
        # TODO require(denorm >= MIN_WEIGHT, "ERR_MIN_WEIGHT")
        # TODO require(denorm <= MAX_WEIGHT, "ERR_MAX_WEIGHT")
        # TODO require(balance >= MIN_BALANCE, "ERR_MIN_BALANCE")
        old_weight = self._records[token].denorm
        if denorm > old_weight:
            self.total_weight = self.total_weight + (denorm - old_weight)
            # TODO if total_weight <= MAX_TOTAL_WEIGHT, "ERR_MAX_TOTAL_WEIGHT")
        elif denorm < old_weight:
            self.total_weight = self.total_weight + (old_weight - denorm)
        self._records[token].denorm = denorm
        # old_balance = self._records[token].balance
        self._records[token].balance = balance
        # TODO simulate token exit fees and transfers for rebind?
        # if balance > old_balance:
        #     NOTE: we are not simulating token transfer yet
        #     _pullUnderlying(token, msg.sender, bsub(balance, old_balance))
        #     pass
        # elif balance < old_balance:
        #     # In this case liquidity is being withdrawn, so charge EXIT_FEE
        #     uint tokenBalanceWithdrawn = bsub(old_balance, balance)
        #     uint tokenExitFee = bmul(tokenBalanceWithdrawn, EXIT_FEE)
        #     _pushUnderlying(token, msg.sender, bsub(tokenBalanceWithdrawn, tokenExitFee))
        #     _pushUnderlying(token, _factory, tokenExitFee)

    def unbind(self):
        # TODO check need for this
        pass

    def get_spot_price(self, token_in: str, token_out: str) -> Decimal:
        min_pool_amount_out = self._records[token_in]
        out_record = self._records[token_out]
        return self.calc_spot_price(min_pool_amount_out.balance, min_pool_amount_out.denorm, out_record.balance, out_record.denorm, self._swap_fee)

    def get_spot_price_sans_fee(self, token_in: str, token_out: str) -> Decimal:
        min_pool_amount_out = self._records[token_in]
        out_record = self._records[token_out]
        return self.calc_spot_price(min_pool_amount_out.balance, min_pool_amount_out.denorm, out_record.balance, out_record.denorm, Decimal('0'))

    def join_pool(self, pool_amount_out: Decimal, max_amounts_in: dict) -> Decimal:
        # TODO
        # require(_finalized, "ERR_NOT_FINALIZED")
        ratio = pool_amount_out / self.pool_token_supply
        # TODO require(ratio != 0, "ERR_MATH_APPROX")

        for token in self._records:
            record = self._records[token]
            token_amount_in = ratio * record.balance
            # TODO require(token_amount_in != 0, "ERR_MATH_APPROX")
            if token_amount_in > max_amounts_in[token]:
                raise Exception('ERR_LIMIT_IN')
            record.balance += token_amount_in
            # TODO: balances of the rest of tokens should be pulled
            # _pullUnderlying(t, msg.sender, token_amount_in)
        self._mint_pool_share(pool_amount_out)
        return pool_amount_out

    def exit_pool(self, pool_amount_in: Decimal, min_amounts_out: dict) -> dict:
        pool_total = self.pool_token_supply
        exit_fee = pool_amount_in * EXIT_FEE
        pool_amount_in_afer_exit_fee = pool_amount_in - exit_fee
        ratio = pool_amount_in_afer_exit_fee / pool_total

        return_dict = {
          "exit_fee_pool_token": exit_fee
        }
        self._burn_pool_share(pool_amount_in_afer_exit_fee)
        
        for token in self._records:
            record = self._records[token]
            token_amount_out = ratio * record.balance
            if token_amount_out == 0:
                raise Exception("ERR_MATH_APPROX")
            if token_amount_out < min_amounts_out[token]:
                raise Exception("ERR_LIMIT_OUT")
            record.balance -= token_amount_out
            return_dict[token] = token_amount_out
        return return_dict
    
    def swap_exact_amount_in(self, token_in: str, token_amount_in: Decimal, token_out: str, min_amount_out: Decimal, max_price: Decimal) -> SwapInResult:
        min_pool_amount_out = self._records[token_in]
        if not min_pool_amount_out.bound:
            raise Exception('ERR_NOT_BOUND')
        out_record = self._records[token_out]
        if not out_record.bound:
            raise Exception('ERR_NOT_BOUND')

        if token_amount_in > min_pool_amount_out.balance * MAX_IN_RATIO:
            raise Exception("ERR_MAX_IN_RATIO")


        spot_price_before = self.calc_spot_price(
                                    token_balance_in=min_pool_amount_out.balance,
                                    token_weight_in=min_pool_amount_out.denorm,
                                    token_balance_out=out_record.balance,
                                    token_weight_out=out_record.denorm,
                                    swap_fee=self._swap_fee
                                )

        if spot_price_before > max_price:
            raise Exception("ERR_BAD_LIMIT_PRICE")
        token_amount_out = self.calc_out_given_in(
                            token_balance_in=min_pool_amount_out.balance,
                            token_weight_in=min_pool_amount_out.denorm,
                            token_balance_out=out_record.balance,
                            token_weight_out=out_record.denorm,
                            token_amount_in=token_amount_in,
                            swap_fee=self._swap_fee
                            )
        # TODO require(token_amount_out >= min_amount_out, "ERR_LIMIT_OUT")

        min_pool_amount_out.balance += token_amount_in
        out_record.balance -= token_amount_out

        spot_price_after = self.calc_spot_price(
                                token_balance_in=min_pool_amount_out.balance,
                                token_weight_in=min_pool_amount_out.denorm,
                                token_balance_out=out_record.balance,
                                token_weight_out=out_record.denorm,
                                swap_fee=self._swap_fee
                           )
        # TODO do we need this safety checks
        if spot_price_after < spot_price_before:
            raise Exception("ERR_MATH_APPROX")
        if spot_price_after > max_price:
            raise Exception("ERR_LIMIT_PRICE")
        if spot_price_before > (token_amount_in / token_amount_out):
            raise Exception("ERR_MATH_APPROX")
        # NOTE: we are not doing user balances yet
        # _pullUnderlying(token_in, msg.sender, token_amount_in)
        # _pushUnderlying(token_out, msg.sender, token_amount_out)
        return SwapInResult(token_amount_out, spot_price_after)

    
    def swap_exact_amount_out(self, token_in: str, max_amount_in: Decimal, token_out: str, token_amount_out: Decimal, max_price: Decimal) -> SwapOutResult:
        min_pool_amount_out = self._records[token_in]
        if not min_pool_amount_out.bound:
            raise Exception('ERR_NOT_BOUND')
        out_record = self._records[token_out]
        if not out_record.bound:
            raise Exception('ERR_NOT_BOUND')

        if token_amount_out > (out_record.balance * MAX_OUT_RATIO):
            raise Exception("ERR_MAX_OUT_RATIO")

        spot_price_before = self.calc_spot_price(
                                token_balance_in=min_pool_amount_out.balance,
                                token_weight_in=min_pool_amount_out.denorm,
                                token_balance_out=out_record.balance,
                                token_weight_out=out_record.denorm,
                                swap_fee=self._swap_fee
                            )
        if spot_price_before > max_price:
            raise Exception('ERR_BAD_LIMIT_PRICE')
        
        token_amount_in = self.calc_in_given_out(
            token_balance_in=min_pool_amount_out.balance,
            token_weight_in=min_pool_amount_out.denorm,
            token_balance_out=out_record.balance,
            token_weight_out=out_record.denorm,
            token_amount_out=token_amount_out,
            swap_fee=self._swap_fee
        )
        if token_amount_in > max_amount_in:
            raise Exception('ERR_LIMIT_IN')

        min_pool_amount_out.balance += token_amount_in
        out_record.balance -= token_amount_out

        spot_price_after = self.calc_spot_price(
            token_balance_in=min_pool_amount_out.balance,
            token_weight_in=min_pool_amount_out.denorm,
            token_balance_out=out_record.balance,
            token_weight_out=out_record.denorm,
            swap_fee=self._swap_fee
            )
        if spot_price_after < spot_price_before:
            raise Exception('ERR_MATH_APPROX')
        if spot_price_after > max_price:
            raise Exception('LIMIT PRICE')
        if spot_price_before > (token_amount_in / token_amount_out):
            raise Exception('ERR_MATH_APPROX')

        # NOTE not modeling balance change for sender
        # _pullUnderlying(token_in, msg.sender, token_amount_in)
        # _pushUnderlying(token_out, msg.sender, token_amount_out)

        return SwapOutResult(token_amount_in=token_amount_in, spot_price_after=spot_price_after)

   
    # @notice Join by swapping a fixed amount of an external token in (must be present in the pool)
    #        System calculates the pool token amount
    # @notice CAN'T BE USED IN SMART POOLS (not finalized)
    # @dev emits a LogJoin event
    # @param tokenIn - which token we're transferring in
    # @param tokenAmountIn - amount of deposit
    # @param minPoolAmountOut - minimum of pool tokens to receive
    # @return poolAmountOut - amount of pool tokens minted and transferred
    def join_swap_extern_amount_in(self, token_in: str, token_amount_in: Decimal, min_pool_amount_out: Decimal) -> Decimal:
        # require(_finalized, "ERR_NOT_FINALIZED");
        if not self._records[token_in].bound:
            raise Exception("ERR_NOT_BOUND")
        if token_amount_in > self._records[token_in].balance *  MAX_IN_RATIO:
            raise Exception("ERR_MAX_IN_RATIO")
    
        in_record = self._records[token_in]

        pool_amount_out = self.calc_pool_out_given_single_in(
            token_balance_in=in_record.balance,
            token_weight_in=in_record.denorm,
            pool_supply=self.pool_token_supply,
            total_weight=self.total_weight,
            token_amount_in=token_amount_in,
            swap_fee=self._swap_fee
        )

        if pool_amount_out < min_pool_amount_out:
            raise Exception("ERR_LIMIT_OUT")

        in_record.balance += token_amount_in

        self._mint_pool_share(pool_amount_out)
        # NOTE user balance can be inferred from params (substract tai), pool out is already returning
        # _pushPoolShare(msg.sender, pool_amount_out);
        # _pullUnderlying(token_in, msg.sender, token_amount_in);
        return pool_amount_out

    

    def join_swap_pool_amount_out(self, token_in: str, pool_amount_out: Decimal, max_amount_in: Decimal) -> Decimal:
        if not self._records[token_in].bound:
            raise Exception("ERR_NOT_BOUND")
        
        in_record = self._records[token_in]

        token_amount_in = self.calc_single_in_given_pool_out(
          token_balance_in = in_record.balance,
          token_weight_in = in_record.denorm,
          pool_supply = self.pool_token_supply,
          total_weight = self.total_weight,
          pool_amount_out = pool_amount_out,
          swap_fee = self._swap_fee)

        if token_amount_in == 0:
          raise Exception("ERR_MATH_APPROX")

        if token_amount_in > max_amount_in:
          raise Exception("ERR_LIMIT_IN")

        if token_amount_in > in_record.balance * MAX_IN_RATIO:
          raise Exception("ERR_MAX_IN_RATIO")
        
        in_record.balance = in_record.balance + token_amount_in
        self._mint_pool_share(pool_amount_out)
        # _pushPoolShare(msg.sender, poolAmountOut);
        # _pullUnderlying(tokenIn, msg.sender, tokenAmountIn);

        return token_amount_in
        