import os 

DEVELOPER_CHAT_ID = 1464783645

class ArbitrageBot():
    token = "1898855073:AAG5061qolcKCpr9ue8K0VeXbCGa9X9HxYg"

class Quandl(): 
    token = "V73FcVhuKu5svV7-sCfk"

class ArbitrageFinder():
    krw_threshold = 0.02
    eur_threshold = 0.08

    job_run_interval = 60 # 1 minute

    save_path = ".\\Resources\\"
    threshold_filename = "thresholds.json"
    thresholds_save_path = os.path.join(save_path, threshold_filename)
