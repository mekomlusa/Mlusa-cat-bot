#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Simple Bot to reply to Telegram messages
# This program is dedicated to the public domain under the CC0 license.
"""
This Bot uses the Updater class to handle the bot.
First, a few handler functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.
Usage:
Basic Echobot example, repeats messages.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, InlineQueryHandler, Job
#import telegram
import logging
import random
import pandas
from uuid import uuid4
import datetime

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

cats = pandas.read_csv("catimage.csv",sep=',',header=None)
alertFlag = {}

# Command handlers
# To start a bot
def start(bot, update):
    update.message.reply_text("""Hi! I'm a cat bot. I can send you a random cat photo daily. \nCheck out /help for all available commands now.\nI'm still under development. Stay tuned!""")

# Helper function
def help(bot, update):
    update.message.reply_text("""/start: to start the bot\n/catphoto: to get a random cat photo \n/comment: to send a comment to the developer.\n"""
                              """/dailyalerton: once turn on, I will send you a random cat photo daily. \n/dailyalertoff: stop pushing cat photo daily if previously turned on.\nAll other messages: I will respond in the future! \nFor all questions please contact dev @mlusaaa""")

# For users to manually retrieve a cat photo    
def catphoto(bot, update):
    rint = random.randint(0,len(cats)-1)
    update.message.reply_photo(cats.ix[rint][1])

# daily update of a cat pic
def dailyalerton(bot, update, job_queue, chat_data):
    user = update.message.from_user
    user_chat_id = update.message.chat_id
    update.message.reply_text('Daily alert turns ON. I will send you a cat photo every 24 hours.\n'
                              'Reply /DailyAlertOff to turn daily photo push off, or /help to check out all other command.')
    logger.info("Daily alert turned ON for %s, ID %s" % (user.first_name, user_chat_id))
    bot.send_message(chat_id='112839673', text="Daily alert turned ON for %s, ID %s" % (user.first_name, user_chat_id))
    alertFlag[user_chat_id]='Y'
    # Add job to queue
    job = job_queue.run_daily(scheduleCat, datetime.datetime.now(), context=user_chat_id)
    chat_data['job'] = job
    
# Turn off daily update of a cat pic    
def dailyalertoff(bot, update, chat_data):
    user = update.message.from_user
    user_chat_id = update.message.chat_id
    
    #Removes the job if the user changed their mind
    if 'job' not in chat_data:
        update.message.reply_text("You don't have daily alert turn on!")
        return
    job = chat_data['job']
    job.schedule_removal()
    del chat_data['job']
    
    update.message.reply_text('Daily alert turns OFF. No cat photo will be auto pushed.\n'
                              'Reply /DailyAlertOn to turn daily photo push on, or /help to check out all other command.')
    logger.info("Daily alert turned OFF for %s, ID %s" % (user.first_name, user_chat_id))
    bot.send_message(chat_id='112839673', text="Daily alert turned OFF for %s, ID %s" % (user.first_name, user_chat_id))
    alertFlag[user_chat_id]='N'

# The function to be called when daily cat alert is on    
def scheduleCat(bot, job):
    rint = random.randint(0,len(cats)-1)
    bot.send_photo(job.context, photo=cats.ix[rint][1])

# Feedback to the dev    
def comment(bot, update, args):
    txt = ' '.join(args)
    if len(txt) == 0:
        update.message.reply_text("""ERROR!! No input was received.""")
    else:
        update.message.reply_text("""Thanks for your feedback! I'll take it :)""")
        newinfo = "New feedback received! From: "+update.message.from_user.username+", Content: "+txt
        bot.send_message(chat_id='112839673', text=newinfo)

# Log all errors
def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))

# Handles all unknown commands   
def unknown(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="ERROR!! Sorry, I didn't understand that command. Please try again!")

# Inline handling - under devlopment
#def inlinequery(bot, update):
#    query = update.inline_query.query
##    results = list()
##
##    results.append(InlineQueryResultArticle(id=uuid4(),
##                                            title="Caps",
##                                            input_message_content=InputTextMessageContent(
##                                                query.upper())))
#
#    #update.inline_query.answer(results)
#    update.inline_query.answer(InlineQueryResultArticle(id=uuid4(),title="Caps",input_message_content=InputTextMessageContent(query.upper())))
#    #update.message.reply_photo("https://drive.google.com/file/d/0BylaRC6E32UxcVZfYjAxWTRpZ3M/view?usp=sharing")

def main():
    # Create the EventHandler and pass it your bot's token.
    updater = Updater("397745204:AAE9aPyJ16MHm1W_IP4JgpeijEy8KVqs6zc")

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler('Catphoto',catphoto))
    dp.add_handler(CommandHandler('Comment', comment, pass_args=True))
    dp.add_handler(CommandHandler('DailyAlertOn',dailyalerton, pass_job_queue=True,
                                  pass_chat_data=True))
    dp.add_handler(CommandHandler('DailyAlertOff',dailyalertoff,pass_chat_data=True))

    # on noncommand i.e message
    dp.add_handler(MessageHandler(Filters.command, unknown))
    
    # Inline query handling
#    dp.add_handler(InlineQueryHandler(inlinequery))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()