
import quandl 
import config

quandl.ApiConfig.api_key = config.Quandl.token 

class FXTickers():
    EURKRW = "EURKRW"

def today_price(ticker:str='EURKRW')->float:
    api_key = "ECB/{}".format(ticker)
    return quandl.get(api_key, rows=1)
