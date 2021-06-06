import logging
import ArbitrageFinder 
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import ConversationHandler
from config import DEVELOPER_CHAT_ID
from config import ArbitrageFinder as FinderConfig
import DataSource.Exceptions as DataExceptions

logger = logging.getLogger(__name__)

class ThresholdChangeStates():
    ask_krw_over_eur = 1
    recv_krw_over_eur = 2
    ask_eur_over_krw = 3
    recv_eur_over_krw = 4 
    cancel = 0

class MarkupKeyboard():
    CONFIRM = "Confirm"
    REENTER = "Re-enter"

class MessageTemplates():

    UNKNOWN_CMD = \
        """Command was not recognised. Use /help to view the commands you can use."""

    UNEXPECTED_ERROR = \
        "Unexpected error has occurred"

    NEW_KRW_OVER_EUR_PROMPT = \
        """Please specify the following:
        Threshold value for Korean price being higher than European price (in %)"""

    NEW_EUR_OVER_KRW_PROMPT = \
        """Please specify the following: 
        Threshold value for European price being higher than Korean price (in %)"""

    SKIP_KRW_OVER_EUR_PROMPT = \
        """Skipping threshold change for KRW over EUR"""

    SKIP_EUR_OVER_KRW_PROMPT = \
        """Skipping threshold change for EUR over KRW"""

    CANCELLATION_PROMPT = "Threshold change cancelled."

    HELP = """Commands: 
    /start - Tell ArbitrageBot to start looking for new opportunities. 
    /change_threshold - Change the threshold values used for finding new opportunities.
    Values need to be in percentage. E.g. 8.0, 15, not 0.08, 0.15"""

    PAUSE = """Pausing message service. To restart, please use the /start command."""

class ArbCallbacks():

    def __init__(self) -> None:
        self.model = ArbitrageFinder.get_model()
        self.job = None 
        self.check_val_perc_not_dec = False 

        self.threshold_change_state = {
            "KRW_OVER_EUR" : 1,
            "EUR_OVER_KRW" : 2
        }

    def help(self, update, context):
        context.bot.send_message(chat_id=update.effective_chat.id, text=MessageTemplates.HELP)

    def unknown_cmd(self, update, context):
        context.bot.send_message(chat_id=update.effective_chat.id, text=MessageTemplates.UNKNOWN_CMD)

    def pause(self, update, context):
        CHAT_ID = update.effective_chat.id 
        job_name = str(CHAT_ID)
        self.remove_arb_jobs(job_name, context)
        context.bot.send_message(chat_id=CHAT_ID, text=MessageTemplates.PAUSE)

    def start(self, update, context):
        CHAT_ID = update.effective_chat.id

        logger.debug("Arbitrage Bot start method called")

        msg = "Adding arbModel.find_arbitrage_opportunity to queue"
        logger.debug(msg)
        
        context.bot.send_message(
            chat_id=CHAT_ID, 
            text=f"""Model params: 
        Thresholds: 
            EUR Over KRW : {self.model.eur_over_krw_threshold*100}%
            KRW Over EUR : {self.model.krw_over_eur_threshold*100}%""")

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
        job_name = str(CHAT_ID)
        self.remove_arb_jobs(job_name, context)

        update.message.reply_text(MessageTemplates.NEW_KRW_OVER_EUR_PROMPT)
        logger.debug(f"Returning next state {ThresholdChangeStates.recv_krw_over_eur}")

        return ThresholdChangeStates.recv_krw_over_eur

    def receive_threshold_krw_over_eur(self, update, context):
        
        logger.debug("Received new krw over eur threshold value")

        userText = update.message.text # handle percentage symbol 

        # check if user text is valid 
        try: 
            threshVal = float(userText)
        except ValueError: 

            if userText == "/skip":
                update.message.reply_text(MessageTemplates.SKIP_KRW_OVER_EUR_PROMPT)
                update.message.reply_text(MessageTemplates.NEW_EUR_OVER_KRW_PROMPT)
                return ThresholdChangeStates.ask_eur_over_krw
            
            update.message.reply_text(
                f"{userText} not recognised as a valid number. Please try again"
            )
            # return to this state
            return ThresholdChangeStates.recv_krw_over_eur

        new_thresh = threshVal
        old_thresh = self.model.krw_over_eur_threshold * 100

        # value needs to be decimal
        self.model.update_krw_over_eur_threshold(new_thresh / 100)

        update.message.reply_text(
            "Changed threshold for Korean price being higher" + 
            f"than European price from {old_thresh} to {new_thresh}")

        update.message.reply_text(MessageTemplates.NEW_EUR_OVER_KRW_PROMPT)

        return ThresholdChangeStates.ask_eur_over_krw

    def ask_threshold_eur_over_krw(self, update, context):
        
        logger.debug("Asking for new eur over krw threshold")

        userText = update.message.text 

        try: 
            new_thresh = float(userText)
            old_thresh = self.model.eur_over_krw_threshold * 100 # to percentage
                
            # val needs to be decimal
            self.model.update_eur_over_krw_threshold(new_thresh/100)

            update.message.reply_text(
                "Changed threshold for European price being higher" + 
                f"than Korean price from {old_thresh}% to {new_thresh}%")

        except ValueError: 
            if userText == "/skip":
                update.message.reply_text(MessageTemplates.SKIP_EUR_OVER_KRW_PROMPT)
            else: 
                update.message.reply_text(
                    f"{userText} not recognised as a valid number. Please try again"
                )
                return ThresholdChangeStates.ask_eur_over_krw

        keyboard_entry = [MarkupKeyboard.CONFIRM, MarkupKeyboard.REENTER]
        update.message.reply_text(
            f"""Please confirm the new thresholds: 
            EUR greater than KRW : {self.model.eur_over_krw_threshold * 100}%
            KRW greater than EUR : {self.model.krw_over_eur_threshold * 100}%""",
            reply_markup=ReplyKeyboardMarkup([keyboard_entry], one_time_keyboard=True)
        )

        return ThresholdChangeStates.recv_eur_over_krw

    def receive_threshold_eur_over_krw(self, update, context): 
        logger.debug("Received new eur over krw threshold")
        response = update.message.text

        if response == MarkupKeyboard.CONFIRM: 
            logger.debug("Ending conversation handler")
            update.message.reply_text("Your threshold changes have been saved")

            ArbitrageFinder.save_thresholds(FinderConfig.thresholds_save_path, self.model)

            # restart arb job with new thresholds 
            self.start(update, context)

            return ConversationHandler.END

        elif response == MarkupKeyboard.REENTER: 
            logger.debug("Going back to entry point")
            update.message.reply_text("Send any message to restart")
            return ThresholdChangeStates.ask_krw_over_eur

    def skip_threshold_krw_over_eur(self, update, context):
        logger.debug("Skipping new KRW over EUR threshold")
        update.message.reply_text(MessageTemplates.SKIP_KRW_OVER_EUR_PROMPT)
        return ThresholdChangeStates.ask_eur_over_krw

    def skip_threshold_eur_over_krw(self, update, context):
        logger.debug("Skipping EUR over KRW threshold")
        update.message.reply_text(MessageTemplates.SKIP_EUR_OVER_KRW_PROMPT)
        return ConversationHandler.END 

    def cancel_change_threshold(self, update, context):
        user = update.message.from_user
        logger.info(f"User {user} cancelled threshold change")
        update.message.reply_text(MessageTemplates.CANCELLATION_PROMPT)
        return ConversationHandler.END

def unknown_error_handler(update:object, context:"CallbackContext") -> None: 
    msg = MessageTemplates.UNEXPECTED_ERROR
    traceback_str = DataExceptions.get_traceback_str(context.error)
    dev_msg = msg + "\n" + traceback_str
    
    context.bot.send_message(chat_id=DEVELOPER_CHAT_ID, text=dev_msg)

    user_msg = MessageTemplates.UNEXPECTED_ERROR + "\n" + \
        "Please restart the bot by using the /start command." + \
        "If the issue persists, please try restarting the ArbitrageBot service on your laptop."
    
    all_users = context.dispatcher.user_data.keys() if update is None else [update.effective_chat.id]
    for user in all_users: 
        if user == DEVELOPER_CHAT_ID:
            break
        context.bot.send_message(chat_id=user, text=user_msg)

    return None 

def error_handler(update:object, context:"CallbackContext"):
    unknown_error_handler(update, context)
    