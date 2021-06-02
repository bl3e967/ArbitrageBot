import pyupbit 

class UpbitTickers():
    XRPKRW = "KRW-XRP"

def today_price(ticker:UpbitTickers)->float:
    return pyupbit.get_current_price(ticker=ticker)
    