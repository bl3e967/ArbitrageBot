import datetime 
import krakenex
from pykrakenapi.pykrakenapi import CallRateLimitError, KrakenAPIError 
import DataSource.Exceptions as DataExceptions
from pykrakenapi import KrakenAPI
from requests import HTTPError

api = krakenex.API()
kraken = KrakenAPI(api)

class KrakenTickers():
    XRPEUR = "XRPEUR"

def today_price(ticker:KrakenTickers) -> float:
    '''
    Return mid price for instrument. 
    Args:  
        instr: str, ticker 
    Returns: 
        mid-price from OHLC data. 
    '''
    try: 
        ohlc, _ = kraken.get_ohlc_data(ticker, interval=1)
    except (HTTPError, KrakenAPIError, CallRateLimitError) as e:
        raise DataExceptions.KrakenConnectionError from e
    
    last_ohlc = ohlc.head(1)
    
    # access single row df with iloc method
    price = ((last_ohlc.high + last_ohlc.low) / 2).iloc[0]

    if not isinstance(price, (int, float)):
        msg = f"No price was provided by Kraken at {datetime.datetime.now()}"
        raise DataExceptions.KrakenConnectionError(msg)

    return price 
    