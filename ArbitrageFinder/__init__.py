import json 
import logging
from ArbitrageFinder import MessageTemplates
from DataSource import Kraken, FXRate, Upbit
from config import ArbitrageFinder as FinderConfig
from config import DEVELOPER_CHAT_ID
import DataSource.Exceptions as DataExceptions

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
        self.min_thresh_change = 0.005
        
        self._last_opp_dict = {
            EnumArbOpportuity.EUR2KRW : self.get_NoArbOpp(),
            EnumArbOpportuity.KRW2EUR : self.get_NoArbOpp()
        }
        
        self._msg_sent_cnt_dict = {
            EnumArbOpportuity.EUR2KRW : 0,
            EnumArbOpportuity.KRW2EUR : 0
        }

        self.msg_sent_cnt = 0 

    def get_thresholds(self)->dict:
        '''Returns dictionary containing threshold values'''
        return {
            "KRW_OVER_EUR" : self.krw_over_eur_threshold, 
            "EUR_OVER_KRW" : self.eur_over_krw_threshold,
            "MIN_THRESH_CHANGE" : self.min_thresh_change
        }

    def get_NoArbOpp(self):
        '''
        Return a default ArbOpp object that has no opportunity. 
        EURKRW needs to be non-zero to prevent division-by-zero error. 
        '''
        return ArbitrageOpportunity(arb_val=0, eur_price=0, 
                                    krw_price=0, eurkrw=1, 
                                    instrname=Instrument("None", "None"))

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

    def should_we_send_message(self, arbOpp:ArbitrageOpportunity) -> bool: 
        '''
        Check if we should send a message: 
            - Check if the opportunity size is significantly different that previous one
              for which last message was sent. 
        
        Args: 
            arbOpp : (ArbitrageOpportunity), latest arbitrage opportunity. 
        
        Returns: 
            opp_sigf : (bool), is the opportunity is significant enough? 
        '''
        _LAST_OPP = self._last_opp_dict[arbOpp.direction]
        _MSG_SENT_CNT = self._msg_sent_cnt_dict[arbOpp.direction]

        # if we have never sent a message yet, then send it.
        if _MSG_SENT_CNT == 0: 
            self._last_opp_dict[arbOpp.direction] = arbOpp 
            return True 
        
        diff = abs(_LAST_OPP.value - arbOpp.value)

        # check if size of opp has changed significantly 
        opp_sigf = diff > self.min_thresh_change

        if opp_sigf: 
            self._last_opp_dict[arbOpp.direction] = arbOpp

        return opp_sigf  
    
    def purge_last_opp(self):
        self._last_opp_dict[EnumArbOpportuity.EUR2KRW] = self.get_NoArbOpp()
        self._last_opp_dict[EnumArbOpportuity.KRW2EUR] = self.get_NoArbOpp()

    def purge_msg_cnts(self):
        self._msg_sent_cnt_dict[EnumArbOpportuity.EUR2KRW] = 0
        self._msg_sent_cnt_dict[EnumArbOpportuity.KRW2EUR] = 0

    def run(self, context):
        job = context.job

        try: 
            arbOpp = self.find_arbitrage_opportunity()
        except DataExceptions.BaseDataConnectionError as e:

            # send message to user 
            context.bot.send_message(job.context, text=str(e))

            # send message to dev 
            tb_str = DataExceptions.get_traceback_str(e)
            dev_msg = str(e) + "\n" + tb_str
            context.bot.send_message(DEVELOPER_CHAT_ID, text=dev_msg)
            return None 

        logger.debug(f"\nArbitrage opportunity: \nValue: {arbOpp.value}\nBuy {arbOpp.buy_currency}\nSell {arbOpp.sell_currency}")

        opp_found = arbOpp.direction != EnumArbOpportuity.NOOP 

        if opp_found:

            # check if this opportunity is significantly different to last one
            # or if the direction is different. We want to prevent spamming the 
            # user every minute when the opportunity has not changed much. 
            send_message = self.should_we_send_message(arbOpp)

            if send_message: 
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
                self._msg_sent_cnt_dict[arbOpp.direction] += 1
        
        else: 
            # If we lose the opportunity, reset this so that we flag the next new opportunity, 
            # even if this is not as big as the previous opportunity. 
            self.purge_last_opp()
            self.purge_msg_cnts()

def get_last_saved_thresholds(fpath):
    '''
    Get last used variable values from file.
    Override krw_threshold and eur_threshold values. 
    Returns: 
        tuple (krw_threshold, eur_threshold)
    '''
    logger.info(f"Getting last saved thresholds from {fpath}")
    
    try:    
        with open(fpath) as json_file: 
            logger.info(f"Loading thresholds from {fpath}")
            thresh_dict = json.load(json_file)
            thresh_tuple = (thresh_dict["KRW_OVER_EUR"], thresh_dict["EUR_OVER_KRW"])
    except FileNotFoundError: 
        logger.info(f"{fpath} not found so loading default thresholds values")
        thresh_tuple = (FinderConfig.krw_threshold, FinderConfig.eur_threshold)

    return thresh_tuple

def save_thresholds(fpath, model:Model):
    '''
    Save model threshold values as json file.
    '''
    thresh_dict = model.get_thresholds()

    with open(fpath, "w") as outfile: 
        json.dump(thresh_dict, outfile)

def get_model():
    fpath = FinderConfig.thresholds_save_path
    krw_threshold, eur_threshold = get_last_saved_thresholds(fpath)
    logger.info(f"Returning new arbitrage model")
    return Model(krw_over_eur_thresh=krw_threshold, 
                 eur_over_krw_thresh=eur_threshold)