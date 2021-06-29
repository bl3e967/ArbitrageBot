import os 
import json
import warnings
import logging 

logger = logging.getLogger(__name__)

DEVELOPER_CHAT_ID = 1464783645

RESOURCES_DIR = ".\\Resources\\"

# !!! If this changes, update .gitignore
DIST_PATH = "./bin/dist/"
WORK_PATH = "./bin/build/"

class Env():
    Prod = "Prod"
    Dev = "Dev"

class ArbitrageBot():
    dev_token = "1898855073:AAG5061qolcKCpr9ue8K0VeXbCGa9X9HxYg"
    prod_token = "1889892335:AAE6Pa1QMUlA30JpfZzfzOpurqy4Lt88ufA"
    token = None 
    config_path = os.path.join(RESOURCES_DIR, "Environment.json")

    @classmethod 
    def get_env(cls):
        with open(cls.config_path) as f: 
            config_dict = json.load(f)
        
        try:
            env = config_dict["ENV"]
            logger.debug(f"Using {env} environment settings")
        except KeyError: 
            logger.warn("No environment details found. Using Dev settings.")
            env = Env.Dev 

        return env 
        
    @classmethod 
    def get_env_token(cls, env:str):

        if env == Env.Prod: 
            return cls.prod_token 
        elif env == Env.Dev: 
            return cls.dev_token 
        else: 
            logger.warn(f"Unrecognised Environment {env}. Defaulting to Dev environment")
            return cls.dev_token 

    @classmethod
    def get_token(cls):
        env = cls.get_env()
        return cls.get_env_token(env)

class Quandl(): 
    token = "V73FcVhuKu5svV7-sCfk"

class ArbitrageFinder():
    buy_eur_sell_krw_thresh = 0.02
    buy_krw_sell_eur_thresh = 0.08

    job_run_interval = 60 # 1 minute

    threshold_filename = "thresholds.json"
    thresholds_save_path = os.path.join(RESOURCES_DIR, threshold_filename)