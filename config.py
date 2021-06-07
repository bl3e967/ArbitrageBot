import os 

DEVELOPER_CHAT_ID = 1464783645

class ArbitrageBot():
    dev_token = "1898855073:AAG5061qolcKCpr9ue8K0VeXbCGa9X9HxYg"
    prod_token = "1889892335:AAE6Pa1QMUlA30JpfZzfzOpurqy4Lt88ufA"

class Quandl(): 
    token = "V73FcVhuKu5svV7-sCfk"

class ArbitrageFinder():
    buy_eur_sell_krw_thresh = 0.02
    buy_krw_sell_eur_thresh = 0.08

    job_run_interval = 60 # 1 minute

    save_path = ".\\Resources\\"
    threshold_filename = "thresholds.json"
    thresholds_save_path = os.path.join(save_path, threshold_filename)
