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

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

#cats = pandas.read_csv("catimage.csv",sep=',',header=None)
alertFlag = {}

# Connect to the database
os.environ['DATABASE_URL'] = "postgres://twgrryvqpbmdeg:b13a294fef6cfbbd246fbb728a0afdd51830440d47d34b6e97c420ad01a2acfa@ec2-54-221-220-82.compute-1.amazonaws.com:5432/d5ieh1gkmiss4t"

urlparse.uses_netloc.append("postgres")
url = urlparse.urlparse(os.environ['DATABASE_URL'])

conn = psycopg2.connect(
    database=url.path[1:],
    user=url.username,
    password=url.password,
    host=url.hostname,
    port=url.port
)

cur = conn.cursor()

# get total cat images available in the library
cur.execute("SELECT count(*) FROM catimage;")
try:
# the cat image library should NOT be empty
    rc = cur.fetchone()
except cur.rowcount == 0:
    raise "No record found in the image library!"
    
# for the cloudinary database
cur.execute("SELECT count(*) FROM photos;")
try:
# the cloudinary library should NOT be empty
    rcc = cur.fetchone()
except cur.rowcount == 0:
    raise "No record found in the Cloudinary image library!"
    
# Command handlers
# To start a bot
def start(bot, update):
    update.message.reply_text("""Hi! I'm a cat bot. I can send you a random cat photo daily. \nCheck out /help for all available commands now.\nI'm still under development. Stay tuned!""")

# Helper function
def help(bot, update):
    update.message.reply_text("""/start: to start the bot\n/catphoto: to get a random cat photo \n/comment: to send a comment to the developer.\n"""
                              """/dailyalerton: once turn on, I will send you a random cat photo daily. \n/dailyalertoff: stop pushing cat photo daily if previously turned on.\nAll other messages: I will respond in the future! \nFor all questions please contact dev @sophielei225""")

# Submit function
def submit(bot, update):
    update.message.reply_text("""Thank you for your willingness to contribute to the cat image library!"""
                              """Upload your pic here: http://bit.ly/2DQyzkV""")

# For users to manually retrieve a cat photo    
def catphoto(bot, update):
    choice = random.randint(0,1)
    if choice == 0:
        # use the traditional cat image library
        rint = random.randint(0,rc[0]-1)
        cur.execute("SELECT * FROM catimage WHERE id = %s;" % (rint))
        pic_selected = cur.fetchone()
        update.message.reply_photo(pic_selected[1])
    else:
        # use cloudinary library to randomly fetch a photo
        rint = random.randint(0,rcc[0]-1)
        cur.execute("SELECT * FROM photos WHERE id = %s;" % (rint))
        pic_selected = cur.fetchone()
        update.message.reply_photo("http://res.cloudinary.com/mlusa/"+pic_selected[2])

# daily update of a cat pic
def dailyalerton(bot, update, job_queue, chat_data):
    user = update.message.from_user
    user_chat_id = update.message.chat_id
    
    # Check to see if daily alert has already been turned on (before cycling)
    if user_chat_id in alertFlag:
        if alertFlag[user_chat_id] == 'Y':
            update.message.reply_text('You have already turned on daily alert. There is no need to turn it on AGAIN.\n'
                                  'Reply /DailyAlertOff to turn daily photo push off, or /help to check out all other command.')
            logger.info(" %s, ID %s attempts to turn on daily alert again while there is already a record on file. (BC)" % (user.first_name, user_chat_id))
            bot.send_message(chat_id='112839673', text="%s, ID %s attempts to turn on daily alert again while there is already a record on file." % (user.first_name, user_chat_id))
            return
    
    # Check to see if daily alert has already been turned on (after cycling)
    cur.execute("SELECT * FROM pushid WHERE status = 'Y';")
    if cur.rowcount > 0:
        result = cur.fetchall()
        ids = list(zip(*result)[0])
        if str(user_chat_id) in ids:
            update.message.reply_text('You have already turned on daily alert. There is no need to turn it on AGAIN.\n'
                                      'Reply /DailyAlertOff to turn daily photo push off, or /help to check out all other command.')
            logger.info(" %s, ID %s attempts to turn on daily alert again while there is already a record on file. (AC)" % (user.first_name, user_chat_id))
            bot.send_message(chat_id='112839673', text="%s, ID %s attempts to turn on daily alert again while there is already a record on file." % (user.first_name, user_chat_id))
            return
        
    # if not then proceed
    update.message.reply_text('Daily alert turns ON. I will send you a cat photo every 24 hours.\n'
                              'Reply /DailyAlertOff to turn daily photo push off, or /help to check out all other command.')
    logger.info("Daily alert turned ON for %s, ID %s" % (user.first_name, user_chat_id))
    bot.send_message(chat_id='112839673', text="Daily alert turned ON for %s, ID %s" % (user.first_name, user_chat_id))
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
    logger.info("Daily alert turned OFF for %s, ID %s" % (user.first_name, user_chat_id))
    bot.send_message(chat_id='112839673', text="Daily alert turned OFF for %s, ID %s" % (user.first_name, user_chat_id))
    alertFlag[user_chat_id]='N'
    
    # Update the database
    #cur.execute("""DELETE FROM pushid WHERE id = %s AND status = 'Y';""", (str(user_chat_id),))
    cur.execute("UPDATE pushid SET status = 'N', eff_date = %s WHERE id = %s AND status = 'Y';", (datetime.datetime.now(),str(user_chat_id)))
    conn.commit()
    
# The function to be called when daily cat alert is on    
def scheduleCat(bot, job):
    choice = random.randint(0,1)
    if choice == 0:
        # use the traditional cat image library
        rint = random.randint(0,rc[0]-1)
        cur.execute("SELECT * FROM catimage WHERE id = %s;" % (rint))
        pic_selected = cur.fetchone()
        bot.send_photo(job.context, photo=pic_selected[1])
    else:
        # use cloudinary library to randomly fetch a photo
        rint = random.randint(0,rcc[0]-1)
        cur.execute("SELECT * FROM photos WHERE id = %s;" % (rint))
        pic_selected = cur.fetchone()
        bot.send_photo(job.context, photo="http://res.cloudinary.com/mlusa/"+pic_selected[2])

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