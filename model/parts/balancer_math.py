from decimal import Decimal

from . import balancer_constants
from .balancer_constants import BONE


class BalancerMath:

    # **********************************************************************************************
    # calcSpotPrice                                                                             //
    # sP = spotPrice                                                                            //
    # bI = token_balance_in                ( bI / wI )         1                                  //
    # bO = token_balance_out         sP =  -----------  *  ----------                             //
    # wI = token_weight_in                 ( bO / wO )     ( 1 - sF )                             //
    # wO = token_weight_out                                                                       //
    # sF = swap_fee                                                                              //
    # **********************************************************************************************/
    @staticmethod
    def calc_spot_price(
            token_balance_in: Decimal,
            token_weight_in: Decimal,
            token_balance_out: Decimal,
            token_weight_out: Decimal,
            swap_fee: Decimal):
        numer = token_balance_in / token_weight_in
        denom = token_balance_out / token_weight_out
        ratio = numer / denom
        scale = 1 / (1 - swap_fee)
        return ratio * scale

    # **********************************************************************************************
    # calcOutGivenIn                                                                            //
    # aO = token_amount_out                                                                       //
    # bO = token_balance_out                                                                      //
    # bI = token_balance_in              /      /            bI             \    (wI / wO) \      //
    # aI = token_amount_in    aO = bO * |  1 - | --------------------------  | ^            |     //
    # wI = token_weight_in               \      \ ( bI + ( aI * ( 1 - sF )) /              /      //
    # wO = token_weight_out                                                                       //
    # sF = swap_fee                                                                              //
    # **********************************************************************************************/
    @staticmethod
    def calc_out_given_in(
            token_amount_in: Decimal,
            token_balance_in: Decimal,
            token_weight_in: Decimal,
            token_balance_out: Decimal,
            token_weight_out: Decimal,
            swap_fee: Decimal):
        weight_ratio = token_weight_in / token_weight_out
        adjusted_in = token_amount_in * (1 - swap_fee)
        y = token_balance_in / (token_balance_in + adjusted_in)
        foo = pow(y, weight_ratio)
        bar = 1 - foo
        token_amount_out = token_balance_out * bar
        return token_amount_out

    # **********************************************************************************************
    # calcInGivenOut                                                                            //
    # aI = token_amount_in                                                                        //
    # bO = token_balance_out               /  /     bO      \    (wO / wI)      \                 //
    # bI = token_balance_in          bI * |  | ------------  | ^            - 1  |                //
    # aO = token_amount_out    aI =        \  \ ( bO - aO ) /                   /                 //
    # wI = token_weight_in           --------------------------------------------                 //
    # wO = token_weight_out                          ( 1 - sF )                                   //
    # sF = swap_fee                                                                              //
    # **********************************************************************************************/

    @staticmethod
    def calc_in_given_out(
            token_balance_out: Decimal,
            token_balance_in: Decimal,
            token_amount_out: Decimal,
            token_weight_in: Decimal,
            token_weight_out: Decimal,
            swap_fee: Decimal):
        weight_ratio = token_weight_out / token_weight_in
        diff = token_balance_out - token_amount_out
        y = token_balance_out / diff
        foo = pow(y, weight_ratio)
        foo = foo - 1
        token_amount_in = 1 - swap_fee
        token_amount_in = (token_balance_in * foo) / token_amount_in
        return token_amount_in

    # **********************************************************************************************
    # calcPoolOutGivenSingleIn                                                                  //
    # pAo = pool_amount_out         /                                              \              //
    # tAi = token_amount_in        ///      /     //    wI \      \\       \     wI \             //
    # wI = token_weight_in        //| tAi *| 1 - || 1 - --  | * sF || + tBi \    --  \            //
    # tW = token_weight     pAo=||  \      \     \\    tW /      //         | ^ tW   | * pS - pS //
    # tBi = token_balance_in      \\  ------------------------------------- /        /            //
    # pS = pool_supply            \\                    tBi               /        /             //
    # sF = swap_fee                \                                              /              //
    # **********************************************************************************************/
    @staticmethod
    def calc_pool_out_given_single_in(
            token_balance_in: Decimal,
            token_weight_in: Decimal,
            pool_supply: Decimal,
            total_weight: Decimal,
            token_amount_in: Decimal,
            swap_fee: Decimal):
        # Charge the trading fee for the proportion of tokenAi
        #  which is implicitly traded to the other pool tokens.
        # That proportion is (1- weightTokenIn)
        # tokenAiAfterFee = tAi * (1 - (1-weightTi) * poolFee)
        normalized_weight = token_weight_in / total_weight
        zaz = (BONE - normalized_weight) * swap_fee
        token_amount_in_after_fee = token_amount_in * (BONE - zaz)

        new_token_balance_in = token_balance_in + token_amount_in_after_fee
        token_in_ratio = new_token_balance_in / token_balance_in

        # new_pool_supply = (ratio_ti ^ weight_ti) * pool_supply
        pool_ratio = pow(token_in_ratio, normalized_weight)
        new_pool_supply = pool_ratio * pool_supply
        pool_amount_out = new_pool_supply - pool_supply
        return pool_amount_out

    # **********************************************************************************************
    # calcSingleInGivenPoolOut                                                                  //
    # tAi = token_amount_in              //(pS + pAo)\     /    1    \\                           //
    # pS = pool_supply                 || ---------  | ^ | --------- || * bI - bI                //
    # pAo = pool_amount_out              \\    pS    /     \(wI / tW)//                           //
    # bI = balanceIn          tAi =  --------------------------------------------               //
    # wI = weightIn                              /      wI  \                                   //
    # tW = token_weight                          |  1 - ----  |  * sF                            //
    # sF = swap_fee                               \      tW  /                                   //
    # **********************************************************************************************/
    @staticmethod
    def calc_single_in_given_pool_out(
            token_balance_in: Decimal,
            token_weight_in: Decimal,
            pool_supply: Decimal,
            total_weight: Decimal,
            pool_amount_out: Decimal,
            swap_fee: Decimal):
        normalized_weight = token_weight_in / total_weight
        new_pool_supply = pool_supply + pool_amount_out
        pool_ratio = new_pool_supply / pool_supply
        # newBalTi = pool_ratio^(1/weightTi) * balTi
        boo = 1 / normalized_weight
        token_ratio = pow(pool_ratio, boo)
        new_token_balance_in = token_ratio * token_balance_in
        token_amount_in_after_fee = new_token_balance_in - token_balance_in
        # Do reverse order of fees charged in joinswap_ExternAmountIn, this way
        #     ``` pAo == joinswap_ExternAmountIn(Ti, joinswap_pool_amount_out(pAo, Ti)) ```
        # tAi = tAiAfterFee / (1 - (1-weightTi) * swap_fee)
        zar = ((1 - normalized_weight) * swap_fee)
        token_amount_in = token_amount_in_after_fee / (1 - zar)
        return token_amount_in

    # **********************************************************************************************
    # calcSingleOutGivenPoolIn                                                                  #
    # tAo = token_amount_out            /      /                                             \\   #
    # bO = token_balance_out           /      # pS - (pAi * (1 - eF)) \     /    1    \      \\  #
    # pAi = pool_amount_in            | bO - || ----------------------- | ^ | --------- | * b0 || #
    # ps = pool_supply                \      \\          pS           /     \(wO / tW)/      #  #
    # wI = tokenWeightIn      tAo =   \      \                                             #   #
    # tW = total_weight                    /     /      wO \       \                             #
    # sF = swap_fee                    *  | 1 - |  1 - ---- | * sF  |                            #
    # eF = exitFee                        \     \      tW /       /                             #
    # **********************************************************************************************/

    @staticmethod
    def calc_single_out_given_pool_in(
            token_balance_out: Decimal,
            token_weight_out: Decimal,
            pool_supply: Decimal,
            total_weight: Decimal,
            pool_amount_in: Decimal,
            swap_fee: Decimal
    ):
        normalized_weight = token_weight_out / total_weight
        # charge exit fee on the pool token side
        # pAiAfterExitFee = pAi*(1-exitFee)

        pool_amount_in_after_exit_fee = pool_amount_in * (1 - balancer_constants.EXIT_FEE)
        new_pool_supply = pool_supply - pool_amount_in_after_exit_fee
        pool_ratio = new_pool_supply / pool_supply
        # newBalTo = pool_ratio ^ (1 / weightTo) * balTo
        token_out_ratio = pow(pool_ratio, (balancer_constants.BONE / normalized_weight))
        new_token_balance_out = token_out_ratio * token_balance_out
        token_amount_out_before_swap_fee = token_balance_out - new_token_balance_out
        # charge swap fee on the output token side
        # tAo = tAoBeforeswap_fee * (1 - (1-weightTo) * swap_fee)
        zaz = (balancer_constants.BONE - normalized_weight) * swap_fee
        token_amount_out = token_amount_out_before_swap_fee * (balancer_constants.BONE - zaz)
        return token_amount_out

    # **********************************************************************************************
    # calcPoolInGivenSingleOut                                                                  //
    # pAi = pool_amount_in               // /               tAo             \\     / wO \     \   //
    # bO = token_balance_out            // | bO - -------------------------- |\   | ---- |     \  //
    # tAo = token_amount_out      pS - ||   \     1 - ((1 - (tO / tW)) * sF)/  | ^ \ tW /  * pS | //
    # ps = pool_supply                 \\ -----------------------------------/                /  //
    # wO = token_weight_out  pAi =       \\               bO                 /                /   //
    # tW = total_weight           -------------------------------------------------------------  //
    # sF = swap_fee                                        ( 1 - eF )                            //
    # eF = exitFee                                                                              //
    # **********************************************************************************************/

    @staticmethod
    def calc_pool_in_given_single_out(
            token_balance_out: Decimal,
            token_weight_out: Decimal,
            pool_supply: Decimal,
            total_weight: Decimal,
            token_amount_out: Decimal,
            swap_fee: Decimal
    ):
        # charge swap fee on the output token side
        normalized_weight = token_weight_out / total_weight
        # tAoBeforeswap_fee = tAo / (1 - (1-weightTo) * swap_fee) 
        zoo = balancer_constants.BONE - normalized_weight
        zar = zoo * swap_fee
        token_amount_out_before_swap_fee = (token_amount_out / (balancer_constants.BONE - zar))
        newtoken_balance_out = token_balance_out - token_amount_out_before_swap_fee
        token_out_ratio = newtoken_balance_out / token_balance_out

        # newpool_supply = (ratioTo ^ weightTo) * pool_supply
        poolRatio = pow(token_out_ratio, normalized_weight)
        newpool_supply = poolRatio * pool_supply
        pool_amount_in_after_exit_fee = pool_supply - newpool_supply

        # charge exit fee on the pool token side
        # pAi = pAiAfterExitFee/(1-exitFee)
        pool_amount_in = pool_amount_in_after_exit_fee / (balancer_constants.BONE - balancer_constants.EXIT_FEE)
        return pool_amount_in
