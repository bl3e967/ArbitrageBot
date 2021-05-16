import logging
import ArbitrageFinder 
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import ConversationHandler
from config import ArbitrageFinder as FinderConfig

logger = logging.getLogger(__name__)

class ThresholdChangeStates():
    ask_krw_over_eur = 1
    recv_krw_over_eur = 2
    ask_eur_over_krw = 3
    recv_eur_over_krw = 4 
    cancel = 0

class ArbCallbacks():

    def __init__(self) -> None:
        self.model = ArbitrageFinder.get_model()
        self.job = None 

        self.threshold_change_state = {
            "KRW_OVER_EUR" : 1,
            "EUR_OVER_KRW" : 2
        }

    def start(self, update, context):
        CHAT_ID = update.effective_chat.id
        context.bot.send_message(chat_id=CHAT_ID, text="Arbitrage Bot start method called")

        msg = "Adding arbModel.find_arbitrage_opportunity to queue"
        logger.debug(msg)
        context.bot.send_message(chat_id=CHAT_ID, text=msg)

        _JOB_TIME_DELAY = 10 # arbitrary 10 second delay for starting the job
        self.job = context.job_queue.run_repeating(callback=self.model.run, 
                                                   interval=FinderConfig.job_run_interval,
                                                   first=_JOB_TIME_DELAY,
                                                   context=CHAT_ID,
                                                   name=str(CHAT_ID))
    
    def remove_arb_jobs(self, name, context) -> bool: 
        current_jobs = context.job_queue.get_jobs_by_name(name)
        if not current_jobs: 
            return False 
        
        for job in current_jobs: 
            job.schedule_removal()

        return True 

    def ask_threshold_krw_over_eur(self, update, context):

        logger.debug("Terminating existing arb jobs")
        CHAT_ID = update.effective_chat.id

        self.remove_arb_jobs(str(CHAT_ID), context)

        update.message.reply_text("Please specify the following:\n" +  
            "Threshold value for Korean price being higher than European price (in %)")

        return ThresholdChangeStates.recv_krw_over_eur

    def receive_threshold_krw_over_eur(self, update, context):
        
        logger.debug("Received new krw over eur threshold value")

        userText = update.message.text # handle percentage symbol 
        new_thresh = float(userText)
        old_thresh = self.model.krw_over_eur_threshold
        update.message.reply_text(
            "Changed threshold for Korean price being higher" + 
            f"than European price from {old_thresh} to {new_thresh}")

        return ThresholdChangeStates.ask_eur_over_krw

    def ask_threshold_eur_over_krw(self, update, context):
        
        logger.debug("Asking for new eur over krw threshold")

        userText = update.message.text 

        update.message.reply_text("Please specify the following:\n" + 
            "Threshold value for European price being higher than Korean price (in %)")

        return ThresholdChangeStates.recv_eur_over_krw

    def receive_threshold_eur_over_krw(self, update, context): 
        
        logger.debug("Received new eur over krw threshold")

        return ConversationHandler.END

    def skip_threshold_krw_over_eur(self, update, context):

        logger.debug("Skipping new krw over eur threshold")
        return ThresholdChangeStates.ask_eur_over_krw

    def skip_threshold_eur_over_krw(self, update, context):

        logger.debug("Skipping eur over krw threshold")
        return ConversationHandler.END 

    def cancel_change_threshold(self, update, context):
        user = update.message.from_user
        logger.info(f"User {user} cancelled threshold change")
        update.message.reply_text(
            "Threshold change cancelled by user"
        )

        return ConversationHandler.END

    




