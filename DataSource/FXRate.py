
import quandl 
import config
import DataSource.Exceptions as DataExceptions

quandl.ApiConfig.api_key = config.Quandl.token 

class FXTickers():
    EURKRW = "EURKRW"

def today_price(ticker:str='EURKRW')->float:
    api_key = "ECB/{}".format(ticker)
    p_df = quandl.get(api_key, rows=1)
    
    if p_df.Value.isnull().iloc[0]:
        msg = f"Quandl returned null value for ticker {ticker}"
        raise DataExceptions.QuandlConnectionError(msg)
    
    return p_df.Value.iloc[0] # we always have one row so iloc is fine here

