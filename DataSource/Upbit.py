import pyupbit 
import datetime
import DataSource.Exceptions as Exceptions

class UpbitTickers():
    XRPKRW = "KRW-XRP"

def today_price(ticker:UpbitTickers)->float:
    curr_price = pyupbit.get_current_price(ticker=ticker)

    if curr_price == None: 
        msg = f"No price was provided by Upbit at {datetime.datetime.now()}." + \
            "Please check if Upbit service is available."
        raise Exceptions.UpbitConnectionError(msg)

    return curr_price 
    