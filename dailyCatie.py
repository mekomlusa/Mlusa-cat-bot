#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Daily catie Bot to send cat photos on Telegram

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, InlineQueryHandler, Job
#import telegram
import logging
import random
import pandas
from uuid import uuid4
import datetime
import os
import psycopg2
import urlparse
import cloudinary.api

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

#cats = pandas.read_csv("catimage.csv",sep=',',header=None)
alertFlag = {}

# Photolist to store photos from the Cloudinary API (instead of calling the API multiple time/connecting to the database):
pl = []

# Connect to the database
urlparse.uses_netloc.append("postgres")
url = urlparse.urlparse(os.environ['DATABASE_URL'])
token = os.environ['TELEGRAM']

conn = psycopg2.connect(
    database=url.path[1:],
    user=url.username,
    password=url.password,
    host=url.hostname,
    port=url.port
)

cur = conn.cursor()
    
# Command handlers
# To start a bot
def start(bot, update):
    update.message.reply_text("""Hi! I'm a cat bot. I can send you a random cat photo daily. \nCheck out /help for all available commands now.\nI'm still under development. Stay tuned!""")

# Helper function
def help(bot, update):
    update.message.reply_text("""/start: to start the bot\n/catphoto: to get a random cat photo \n/comment: to send a comment to the developer.\n"""
                              """/dailyalerton: once turn on, I will send you a random cat photo daily. \n/dailyalertoff: stop pushing cat photo daily if previously turned on.\n/submit: submit your cat photos to the catie library.\n"""
                              """All other messages: I will respond in the future! \nFor all questions please contact dev @sophielei225""")

# Submit function
def submit(bot, update):
	update.message.reply_text("""Submit was temporaily disabled. If you would like to contribute please contact @sophielei225""")
    #update.message.reply_text("""Thank you for your willingness to contribute to the cat image library! """
                              #"""Upload your pic here: http://bit.ly/2DQyzkV""")

# For users to manually retrieve a cat photo    
def catphoto(bot, update):
    rint = random.randint(0,len(pl)-1)
    pic_selected = pl[rint]['secure_url']
    update.message.reply_photo(pic_selected)

# daily update of a cat pic
def dailyalerton(bot, update, job_queue, chat_data):
    user = update.message.from_user
    user_chat_id = update.message.chat_id
    
    # Check to see if daily alert has already been turned on (before cycling)
    if user_chat_id in alertFlag:
        if alertFlag[user_chat_id] == 'Y':
            update.message.reply_text('You have already turned on daily alert. There is no need to turn it on AGAIN.\n'
                                  'Reply /DailyAlertOff to turn daily photo push off, or /help to check out all other command.')
            logger.info(" %s, ID %s, username %s attempts to turn on daily alert again while there is already a record on file. (BC)" % (user.first_name, user_chat_id, user.username))
            bot.send_message(chat_id='112839673', text="%s, ID %s, username %s attempts to turn on daily alert again while there is already a record on file." % (user.first_name, user_chat_id, user.username))
            return
    
    # Check to see if daily alert has already been turned on (after cycling)
    cur.execute("SELECT * FROM pushid WHERE status = 'Y';")
    if cur.rowcount > 0:
        result = cur.fetchall()
        ids = list(zip(*result)[0])
        if str(user_chat_id) in ids:
            update.message.reply_text('You have already turned on daily alert. There is no need to turn it on AGAIN.\n'
                                      'Reply /DailyAlertOff to turn daily photo push off, or /help to check out all other command.')
            logger.info(" %s, ID %s, username %s attempts to turn on daily alert again while there is already a record on file. (AC)" % (user.first_name, user_chat_id, user.username))
            bot.send_message(chat_id='112839673', text="%s, ID %s, username %s attempts to turn on daily alert again while there is already a record on file." % (user.first_name, user_chat_id, user.username))
            return
        
    # if not then proceed
    update.message.reply_text('Daily alert turns ON. I will send you a cat photo every 24 hours.\n'
                              'Reply /DailyAlertOff to turn daily photo push off, or /help to check out all other command.')
    logger.info("Daily alert turned ON for %s, ID %s, username %s" % (user.first_name, user_chat_id, user.username))
    bot.send_message(chat_id='112839673', text="Daily alert turned ON for %s, ID %s, username %s" % (user.first_name, user_chat_id, user.username))
    alertFlag[user_chat_id]='Y'
    
    # Update the database
    cur.execute("SELECT * FROM pushid;")
    if cur.rowcount > 0:
        result = cur.fetchall()
        ids = list(zip(*result)[0])
        if str(user_chat_id) not in ids:
            cur.execute("INSERT INTO pushid (id,status,eff_date) VALUES (%s, %s, %s);", (user_chat_id, 'Y',datetime.datetime.now()))
        else:
            cur.execute("UPDATE pushid SET status = 'Y', eff_date = %s WHERE id = %s AND status = 'N';", (datetime.datetime.now(),str(user_chat_id)))
    conn.commit()
    
    # Add job to queue
    #job = job_queue.run_daily(scheduleCat, datetime.datetime.now(), context=user_chat_id)
    job = job_queue.run_once(scheduleCat, datetime.datetime.now(), context=user_chat_id)
    chat_data['job'] = job
    
# Turn off daily update of a cat pic    
def dailyalertoff(bot, update, chat_data):
    user = update.message.from_user
    user_chat_id = update.message.chat_id
    
    cur.execute("SELECT * FROM pushid WHERE status = 'Y';")
    if cur.rowcount > 0:
        result = cur.fetchall()
        ids = list(zip(*result)[0])
    
    #Removes the job if the user changed their mind
    if 'job' not in chat_data and str(user_chat_id) not in ids:
        update.message.reply_text("You don't have daily alert turn on!")
        return
    # push generated by the cycling, not enabled by the user:
    elif 'job' in chat_data:
        job = chat_data['job']
        job.schedule_removal()
        del chat_data['job']
    
    update.message.reply_text('Daily alert turns OFF. No cat photo will be auto pushed.\n'
                              'Reply /DailyAlertOn to turn daily photo push on, or /help to check out all other command.')
    logger.info("Daily alert turned OFF for %s, ID %s, username %s" % (user.first_name, user_chat_id, user.username))
    bot.send_message(chat_id='112839673', text="Daily alert turned OFF for %s, ID %s, username %s" % (user.first_name, user_chat_id, user.username))
    alertFlag[user_chat_id]='N'
    
    # Update the database
    #cur.execute("""DELETE FROM pushid WHERE id = %s AND status = 'Y';""", (str(user_chat_id),))
    cur.execute("UPDATE pushid SET status = 'N', eff_date = %s WHERE id = %s AND status = 'Y';", (datetime.datetime.now(),str(user_chat_id)))
    conn.commit()
    
# The function to be called when daily cat alert is on    
def scheduleCat(bot, job):
    rint = random.randint(0,len(pl)-1)
    pic_selected = pl[rint]['secure_url']
    bot.send_photo(job.context, photo=pic_selected)
    
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

def main():
    # Create the EventHandler and pass it your bot's token.
    updater = Updater(token, request_kwargs={'read_timeout': 6, 'connect_timeout': 7})
    j = updater.job_queue

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("submit", submit))
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
    updater.start_polling(poll_interval = 1.0,timeout=20)
    
    # Connect to the Cloudinary Admin API
    res = cloudinary.api.resources(cloud_name="mlusa",api_key=os.environ['CLD_API_KEY'],
                                  api_secret=os.environ['CLD_API_SECRET'],
                                  max_results="500")
    pl.extend(res['resources'])
    
    # Once exceed the 500 photos limit
    while 'next_cursor' in res:
        nc = res['next_cursor']
        res = cloudinary.api.resources(cloud_name="mlusa",api_key=os.environ['CLD_API_KEY'],
                                  api_secret=os.environ['CLD_API_SECRET'],
                                  max_results="500")
        pl.extend(res['resources'])
    
    # Existing user check
    cur.execute("SELECT * FROM pushid WHERE status = 'Y';")
    if cur.rowcount > 0:
        result = cur.fetchall()
        ids = list(zip(*result)[0])
        for user in ids:
            #j.run_daily(scheduleCat, datetime.datetime.now(), context=user)
            j.run_once(scheduleCat, datetime.datetime.now(), context=user)

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()
    
    # Close communication with the database
    cur.close()
    conn.close()


if __name__ == '__main__':
    main()