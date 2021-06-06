import logging
from typing import Text 
import ArbitrageFinder 
from ArbitrageBot import callbacks, Regex
from config import ArbitrageBot as BotConfig 
from telegram.ext import (
    Updater, 
    CommandHandler, 
    ConversationHandler,
    MessageHandler,
    Filters
)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)

def run():
    updater = Updater(token=BotConfig.token, use_context=True)
    dispatcher = updater.dispatcher
    
    arbCallback = callbacks.ArbCallbacks()
    start_handler = CommandHandler("start", arbCallback.start)
    
    threshold_change_handler = ConversationHandler(
        entry_points=[CommandHandler('change_threshold', arbCallback.ask_threshold_krw_over_eur)],
        states={
            
            callbacks.ThresholdChangeStates.ask_krw_over_eur : [
                MessageHandler(
                    Filters.text, 
                    arbCallback.ask_threshold_krw_over_eur
                ),
                CommandHandler("skip", arbCallback.skip_threshold_krw_over_eur)
            ],

            callbacks.ThresholdChangeStates.recv_krw_over_eur : [
                MessageHandler(
                    Filters.text,
                    arbCallback.receive_threshold_krw_over_eur
                ),
                CommandHandler("skip", arbCallback.skip_threshold_krw_over_eur)
            ],
                      
            callbacks.ThresholdChangeStates.ask_eur_over_krw : [
                MessageHandler(
                    filters=Filters.text, 
                    callback=arbCallback.ask_threshold_eur_over_krw
                ),
            ],

            callbacks.ThresholdChangeStates.recv_eur_over_krw : [
                MessageHandler(
                    Filters.text,
                    arbCallback.receive_threshold_eur_over_krw
                ),
                CommandHandler("skip", arbCallback.skip_threshold_eur_over_krw)
            ]
        },

        fallbacks=[CommandHandler('cancel', arbCallback.cancel_change_threshold)],

        allow_reentry=True
    )

    # deal with invlaid commands
    unknown_cmd_handler = MessageHandler(Filters.command, arbCallback.unknown_cmd)

    help_handler = CommandHandler("help", arbCallback.help)

    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(threshold_change_handler)
    dispatcher.add_handler(unknown_cmd_handler)

    # error handlers
    dispatcher.add_error_handler(callbacks.error_handler)

    updater.start_polling()
    updater.idle()

if __name__=="__main__":
    run()