from string import Template

newOpportunityFoundMsg = Template(
    """Arbitrage opportunity found for $INSTRNAME

    Buy $BUY_INSTR from $BUY_EXCHG
    Sell $SELL_INSTR from $SELL_EXCHG
    
    European Exchange Price : \u20ac $EX_EUR_P_EUR | \u20a9 $EX_EUR_P_KRW
    Korean Exchange Price   : \u20ac $EX_KRW_P_EUR | \u20a9 $EX_KRW_P_KRW

    Arbitrage Opportunity: $ArbSize %
    """
)