import traceback


class BaseDataConnectionError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class UpbitConnectionError(BaseDataConnectionError):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class KrakenConnectionError(BaseDataConnectionError):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class QuandlConnectionError(BaseDataConnectionError):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

def get_traceback_str(err:Exception) -> str: 
    '''Returns traceback information as string given an Exception.
    Arg: 
        err: Exception object or child of Exception class. 
    
    Returns: 
        tb_string: (str), traceback information.
    '''
    tb_list = traceback.format_exception(None, err, err.__traceback__)
    tb_string = ''.join(tb_list)
    return tb_string 