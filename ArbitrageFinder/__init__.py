import logging
from ArbitrageFinder import MessageTemplates
from DataSource import Kraken, FXRate, Upbit
from config import ArbitrageFinder as FinderConfig

logger = logging.getLogger(__name__)

class EnumArbOpportuity():
    EUR2KRW = 1  # buy in eur and sell in krw 
    KRW2EUR = -1 # buy in krw and sell in eur 
    NOOP = 0 

class Exchanges():
    EUR = "Kraken"
    KRW = "Upbit"

class Currencies():
    EUR = "EUR"
    KRW = "KRW"

class Instrument():
    def __init__(self, base, quote):
        '''
        Instrument BUY_LEG/SELL_LEG
        '''
        self.base = base
        self.quote = quote
        self.ticker = f"{self.base}/{self.quote}"

    def __str__(self):
        return self.ticker 

class EnumInstrumentIDs():
    BTCUSDT = Instrument("BTC", "USDT")
    ETHUSDT = Instrument("ETH", "USDT")
    XRPEUR = Instrument("XRP", "EUR")

class ArbitrageOpportunity():
    def __init__(self, 
                 arb_val:float, 
                 eur_price:float, 
                 krw_price:float, 
                 eurkrw:float, 
                 instrname:Instrument):

        self.instrument = instrname
        self.eurkrw = eurkrw
        self.value = arb_val 
        self.size = abs(arb_val)
        self.direction = 1 if arb_val > 0 else 0 if arb_val == 0 else -1
        
        self.euro_price = eur_price 
        self.euro_price_in_krw = eur_price * eurkrw 

        self.krw_price = krw_price
        self.krw_price_in_eur = krw_price / eurkrw 


        if self.direction == EnumArbOpportuity.EUR2KRW: 
            
            self.buy_price = self.euro_price 
            self.sell_price = self.krw_price

            self.buy_exchg = Exchanges.EUR 
            self.sell_exchg = Exchanges.KRW 

            self.buy_currency = Currencies.EUR 
            self.sell_currency = Currencies.KRW 

            self.buy_instrument = self.instrument.quote 
            self.sell_instrument = self.instrument.base 

        else: 

            self.buy_price = self.krw_price 
            self.sell_price = self.euro_price 

            self.buy_exchg = Exchanges.KRW 
            self.sell_exchg = Exchanges.EUR 

            self.buy_currency = Currencies.KRW 
            self.sell_currency = Currencies.EUR 

            self.buy_instrument = self.instrument.base 
            self.sell_instrument = self.instrument.quote 

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

    def check_if_any_thresh_exceeded(self, val):
        '''
        Check if value has exceeded any threshold
        Returns: 
            Bool, True if magnitude of value is smaller than any
            threshold value, else False. 
        '''
        below_thresh1 = abs(val) < self.krw_over_eur_threshold
        below_thresh2 = abs(val) < self.eur_over_krw_threshold
        return below_thresh1 and below_thresh2 

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

        # get kraken price 
        kraken_eur = Kraken.today_price(ticker=Kraken.KrakenTickers.XRPEUR)

        # get upbit price 
        upbit_krw = Upbit.today_price(ticker=Upbit.UpbitTickers.XRPKRW)

        # get eurkrw exchange rate 
        eurKrwRate = FXRate.today_price(ticker=FXRate.FXTickers.EURKRW)

        # convert upbit price to eur
        upbit_eur = upbit_krw / eurKrwRate

        # check if the price ratio is above/below threshold
        arb_val = kraken_eur / upbit_eur - 1 
        
        if self.check_if_any_thresh_exceeded(arb_val): 
            arb_val = EnumArbOpportuity.NOOP

        return ArbitrageOpportunity(arb_val, 
                                    eur_price=kraken_eur, 
                                    krw_price=upbit_krw, 
                                    eurkrw=eurKrwRate, 
                                    instrname=EnumInstrumentIDs.XRPEUR)

    def run(self, context):
        job = context.job
        arbOpp = self.find_arbitrage_opportunity()

        logger.debug(f"\nArbitrage opportunity: \nValue: {arbOpp.value}\nBuy {arbOpp.buy_currency}\nSell {arbOpp.sell_currency}")

        if arbOpp.direction != EnumArbOpportuity.NOOP:

            _msg = MessageTemplates.newOpportunityFoundMsg.substitute(
                {
                    "INSTRNAME" : arbOpp.instrument,
                    "BUY_INSTR" : arbOpp.buy_instrument, 
                    "SELL_INSTR" : arbOpp.sell_instrument, 
                    "BUY_EXCHG" : arbOpp.buy_exchg, 
                    "SELL_EXCHG" : arbOpp.sell_exchg, 
                    "EX_EUR_P_EUR" : format(arbOpp.euro_price, ".2f"), 
                    "EX_EUR_P_KRW" : format(arbOpp.euro_price * arbOpp.eurkrw, ".2f"), 
                    "EX_KRW_P_EUR" : format(arbOpp.krw_price / arbOpp.eurkrw, ".2f"), 
                    "EX_KRW_P_KRW" : format(arbOpp.krw_price, ".2f"),
                    "ArbSize" : format(arbOpp.size * 100, ".2f") # in percentage %
                }
            )

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