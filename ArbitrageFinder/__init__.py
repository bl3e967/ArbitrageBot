import random
import logging
from config import ArbitrageFinder as FinderConfig

logger = logging.getLogger(__name__)

class EnumArbOpportuity():
    EUR2KRW = 1  # buy in eur and sell in krw 
    KRW2EUR = -1 # buy in krw and sell in eur 
    NOOP = 0 

class Exchanges():
    EUR = "EUR"
    KRW = "KRW"

class Currencies():
    EUR = "EUR"
    KRW = "KRW"

class EnumInstrumentIDs():
    BTCUSDT = "BTCUSDT"
    ETHUSDT = "ETHUSDT"

class ArbitrageOpportunity():
    def __init__(self, arb_val, eur_price, krw_price, instrname):
        self.instrument = instrname
        self.value = arb_val 
        self.size = abs(arb_val)
        self.direction = 1 if arb_val > 0 else 0 if arb_val == 0 else -1
        
        self.euro_price = eur_price 
        self.krw_price = krw_price

        self.buy_price = self.euro_price if self.direction == EnumArbOpportuity.EUR2KRW else self.krw_price
        self.sell_price = self.krw_price if self.direction == EnumArbOpportuity.EUR2KRW else self.euro_price

        self.buy_exchg = Exchanges.EUR if self.direction == EnumArbOpportuity.EUR2KRW else Exchanges.KRW
        self.sell_exchg = Exchanges.KRW if self.direction == EnumArbOpportuity.EUR2KRW else Exchanges.EUR

        self.buy_currency = Currencies.EUR if self.buy_exchg == EnumArbOpportuity.EUR2KRW else Exchanges.KRW
        self.sell_currency = Currencies.KRW if self.buy_exchg == EnumArbOpportuity.EUR2KRW else Exchanges.EUR

class Model():
    '''
    Model to find arbitrage opportunities. 
    '''
    def __init__(self, krw_over_eur_thresh, eur_over_krw_thresh):

        self.job = None 

        self.krw_over_eur_threshold = krw_over_eur_thresh
        self.eur_over_krw_threshold = eur_over_krw_thresh

    def update_krw_over_eur_threshold(self, newval:float) -> None:
        self.krw_over_eur_threshold = newval 

    def update_eur_over_krw_threshold(self, newval:float) -> None:
        self.eur_over_krw_threshold = newval

    def find_arbitrage_opportunity(self):
        '''
        Get coin price data for current datetime.
        Get EUR/KRW exchange rate. 
        Calculate Arbitrage opportunity percentage.
        Return (int)1 if Buy in EUR and sell in KRW
        Return (int)-1 if Buy in KRW and sell in EUR 
        Return (int)0 if not.

        Returns: 
            ArbitrageOpportunity: 
        '''
        choices = [EnumArbOpportuity.EUR2KRW, EnumArbOpportuity.NOOP, EnumArbOpportuity.KRW2EUR]
        p = [0.4, 0.1, 0.5]
        opp = random.choices(choices, p)[0]

        instr = random.choices([EnumInstrumentIDs.BTCUSDT, EnumInstrumentIDs.ETHUSDT], [0.5, 0.5])[0]

        arbSize = abs(random.gauss(0.05,0.03))

        eurprice = random.gauss(50000, 100)
        krwprice = eurprice * (1 + opp*arbSize)

        return ArbitrageOpportunity(opp*arbSize, eur_price=eurprice, krw_price=krwprice, instrname=instr)

    def run(self, context):
        job = context.job
        arbOpp = self.find_arbitrage_opportunity()

        logger.debug(f"Arbitrage opportunity: \n\tValue: {arbOpp.value}\n\tBuy {arbOpp.buy_currency}\n\t{arbOpp.sell_currency}")

        if arbOpp.direction != EnumArbOpportuity.NOOP:

            _msg = f"""Arbitrage Opportunity found for {arbOpp.instrument}
            
            Buy {arbOpp.instrument} in {arbOpp.buy_exchg} exchange
            Sell {arbOpp.instrument} in {arbOpp.sell_exchg} exchange

            {arbOpp.buy_exchg} Exchange {arbOpp.instrument} current price: {arbOpp.buy_price}
            {arbOpp.sell_exchg} Exchange {arbOpp.instrument} current price: {arbOpp.sell_price}
            """

            context.bot.send_message(job.context, text=_msg)

def get_last_saved_thresholds(fname):
    '''
    Get last used variable values from file.
    Override krw_threshold and eur_threshold values. 
    Returns: 
        tuple (krw_threshold, eur_threshold)
    '''
    logger.info(f"Getting last saved thresholds from {fname}")
    return (FinderConfig.krw_threshold, FinderConfig.eur_threshold)

def get_model():
    fname = FinderConfig.save_path
    krw_threshold, eur_threshold = get_last_saved_thresholds(fname)
    logger.info(f"Returning new arbitrage model")
    return Model(krw_over_eur_thresh=krw_threshold, 
                 eur_over_krw_thresh=eur_threshold)