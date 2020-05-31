#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Daily catie Bot to send cat photos on Telegram
# Update 5/2/2020: Python 2.7 to Python 3
# Update 5/5/2020: Added Photo pull functions

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, InlineQueryHandler, Job
import logging
import pandas
from uuid import uuid4
import datetime
import os
import cloudinary.api
import argparse
from telegram.error import (TelegramError, Unauthorized, BadRequest, 
                            TimedOut, ChatMigrated, NetworkError)

from threading import Thread
import sys
from dbhelper import DBHelper
from utilities import CloudinaryHelper

# handle database connections
db = DBHelper(choice='mysql') # change to 'psql' if you're using psql

# handle cloudinary operations
cloudinary_connector = CloudinaryHelper()

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

# Command handlers
# To start a bot
def start(update, context):
    update.message.reply_text("""Hi! I'm a cat bot. I can send you a random cat photo daily. \nCheck out /help for all available commands.\nI'm still under active development. Stay tuned!""")

# Helper function
def help(update, context):
    update.message.reply_text("""/start: to start the bot\n/catphoto: to get a random cat photo \n/comment: to send a comment to the developer.\n"""
                              """/dailyalerton: once turn on, I will send you a random cat photo daily. \n/dailyalertoff: stop pushing cat photo daily if previously turned on.\n"""
                              """All other messages: I will respond in the future! \nFor all questions please contact dev @hanabi_225""")

# Admin helper function
def admin_help(update, context):
    update.message.reply_text("""ADMIN HELPER FUNCTIONS: /pullnewpic: Sync with Cloudinary photo bed.\n/submit: Submit new photos (currently disasbled).\n/broadcast: send broadcast messages to all users.""")


# Submit function
def submit(update, context):
	update.message.reply_text("""Submit was temporaily disabled. If you would like to contribute please contact @hanabi_225""")
    #update.message.reply_text("""Thank you for your willingness to contribute to the cat image library! """
                              #"""Upload your pic here: http://bit.ly/2DQyzkV""")

# For users to manually retrieve a cat photo    
def catphoto(update, context):
    update.message.reply_photo(cloudinary_connector.get_one_random_photo())

# daily update of a cat pic
def dailyalerton(update, context):
    user = update.message.from_user
    user_chat_id = update.message.chat_id
    
    # Check to see if daily alert has already been turned on
    result = db.get_active_users()
    if len(result) > 0:
        if str(user_chat_id) in result:
            update.message.reply_text('You have already turned on daily alert. There is no need to turn it on AGAIN.\n'
                                      'Reply /DailyAlertOff to turn daily photo push off, or /help to check out all other command.')
            logger.info(" %s, ID %s, username %s attempts to turn on daily alert again while there is already a record on file. (AC)" % (user.first_name, user_chat_id, user.username))
            context.bot.send_message(chat_id=os.environ['TELEGRAM_ADMIN_CHATID'], text="%s, ID %s, username %s attempts to turn on daily alert again while there is already a record on file." % (user.first_name, user_chat_id, user.username))
            return
        
    # if not then proceed
    update.message.reply_text('Daily alert turns ON. I will send you a cat photo every 24 hours.\n'
                              'Reply /DailyAlertOff to turn daily photo push off, or /help to check out all other command.')
    logger.info("Daily alert turned ON for %s, ID %s, username %s" % (user.first_name, user_chat_id, user.username))
    context.bot.send_message(chat_id=os.environ['TELEGRAM_ADMIN_CHATID'], text="Daily alert turned ON for %s, ID %s, username %s" % (user.first_name, user_chat_id, user.username))
    
    # Update the database
    get_all_users_list = db.get_all_users()
    if len(get_all_users_list) > 0:
        if str(user_chat_id) not in get_all_users_list:
            db.add_user(str(user_chat_id))
        else:
            db.resurrect_user(str(user_chat_id))
    else: # brand new situation
        db.add_user(str(user_chat_id))
    
    # Add job to queue
    job = context.job_queue.run_daily(scheduleCat, datetime.time(22), context=user_chat_id)
    catphoto(update, context)
    context.chat_data['job'] = job
    
# Turn off daily update of a cat pic    
def dailyalertoff(update, context):
    user = update.message.from_user
    user_chat_id = update.message.chat_id
    
    active_users_list = db.get_active_users()
    
    #Removes the job if the user changed their mind
    if 'job' not in context.chat_data and str(user_chat_id) not in active_users_list:
        update.message.reply_text("You don't have daily alert turn on!")
        return
    # the user previously do have alert turned on
    elif 'job' in context.chat_data:
        job = context.chat_data['job']
        job.schedule_removal()
        del context.chat_data['job']
    
    update.message.reply_text('Daily alert turns OFF. No cat photo will be auto pushed.\n'
                              'Reply /DailyAlertOn to turn daily photo push on, or /help to check out all other command.')
    logger.info("Daily alert turned OFF for %s, ID %s, username %s" % (user.first_name, user_chat_id, user.username))
    context.bot.send_message(chat_id=os.environ['TELEGRAM_ADMIN_CHATID'], text="Daily alert turned OFF for %s, ID %s, username %s" % (user.first_name, user_chat_id, user.username))
    
    # Update the database
    db.soft_delete_user(str(user_chat_id))
    
# The function to be called when daily cat alert is on    
def scheduleCat(context):
    job = context.job
    pic_selected = cloudinary_connector.get_one_random_photo()
    try:
        context.bot.send_photo(job.context, photo=pic_selected)
    except BadRequest:
        print("scheduleCat call failed on",job.context)
        return
    except Unauthorized:
        print("bot is blocked by",job.context)
        return

# DEV MODE: Preiodically check if new photo has been loaded    
def checkIfNewPhotoLoaded(update, context):
    context.bot.send_message(chat_id=os.environ['TELEGRAM_ADMIN_CHATID'], 
                            text='Bot is checking if new image has been added to Cloudinary.')
    last_pull_image_length = cloudinary_connector.get_last_pull_image_length()
    cloudinary_connector.consecutive_pull_from_Cloudinary_server()
    print(last_pull_image_length, cloudinary_connector.get_last_pull_image_length())
    if cloudinary_connector.get_last_pull_image_length() > last_pull_image_length:
        context.bot.send_message(chat_id=os.environ['TELEGRAM_ADMIN_CHATID'], 
                            text='New Photo has been uploaded to Cloudinary. Photo stack updated.')
    else:
        context.bot.send_message(chat_id=os.environ['TELEGRAM_ADMIN_CHATID'], 
                            text='No new photo is detected. Ending task.')
    
# Feedback to the dev    
def comment(update, context):
    txt = ' '.join(context.args)
    if len(txt) == 0:
        update.message.reply_text("""ERROR!! No input was received.""")
    else:
        update.message.reply_text("""Thanks for your feedback! I'll take it :)""")
        newinfo = "New feedback received! From: "+update.message.from_user.username+", Content: "+txt
        context.bot.send_message(chat_id=os.environ['TELEGRAM_ADMIN_CHATID'], text=newinfo)

# Broadcast to the group
def broadcast(update, context):
    txt = ' '.join(context.args)
    if len(txt) == 0:
        update.message.reply_text("""ERROR!! No input was received.""")
    else:
        active_users_list = db.get_active_users()
        for active_user in active_users_list:
            context.bot.send_message(chat_id=active_user, 
                            text="New message from the admin: {}".format(txt))

# Log all errors
def error(update, context):
    logger.warn('Update "%s" caused error "%s"' % (update, context.error))

# Handles all unknown commands   
def unknown(update, context):
    context.bot.send_message(chat_id=update.message.chat_id, text="ERROR!! Sorry, I didn't understand that command yet. Please try again!")

def main():
    # Create the EventHandler and pass it your bot's token.
    updater = Updater(os.environ['TELEGRAM'], use_context=True)
    j = updater.job_queue

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("adminhelp", admin_help, filters=Filters.user(username='@hanabi_225')))
    dp.add_handler(CommandHandler("submit", submit, filters=Filters.user(username='@hanabi_225')))
    dp.add_handler(CommandHandler("pullnewpic", checkIfNewPhotoLoaded, filters=Filters.user(username='@hanabi_225')))
    dp.add_handler(CommandHandler("broadcast", broadcast, filters=Filters.user(username='@hanabi_225')))
    dp.add_handler(CommandHandler('Catphoto',catphoto))
    dp.add_handler(CommandHandler('Comment', comment, pass_args=True))
    dp.add_handler(CommandHandler('DailyAlertOn',dailyalerton))
    dp.add_handler(CommandHandler('DailyAlertOff',dailyalertoff))

    # on noncommand i.e message
    dp.add_handler(MessageHandler(Filters.command, unknown))
    
    # Inline query handling
#    dp.add_handler(InlineQueryHandler(inlinequery))
        
    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling(poll_interval = 1.0,timeout=20)
    
    # Connect to the Cloudinary Admin API
    cloudinary_connector.initial_pull_from_Cloudinary_server()
    
    # Existing user check
    active_users = db.get_active_users()
    if len(active_users) > 0:
        for user in active_users:
            j.run_daily(scheduleCat, time=datetime.time(22), context=user) # hardcoded to be UTC 10 pm everyday
            #j.run_once(scheduleCat, datetime.datetime.now(), context=user)
    
    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()

    # close database connections
    db.close_connection()

if __name__ == '__main__':
    main()