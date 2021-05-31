import krakenex 
from pykrakenapi import KrakenAPI

api = krakenex.API()
kraken = KrakenAPI(api)

class KrakenTickers():
    XRPEUR = "XRPEUR"

def today_price(ticker:KrakenTickers):
    '''
    Return mid price for instrument. 
    Args:  
        instr: str, ticker 
    Returns: 
        mid-price from OHLC data. 
    '''
    ohlc, _ = kraken.get_ohlc_data(ticker, interval=1)
    last_ohlc = ohlc.head(1)
    return (last_ohlc.high + last_ohlc.low) / 2
    