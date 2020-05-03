# source: https://www.codementor.io/@garethdwyer/building-a-chatbot-using-telegram-and-python-part-2-sqlite-databse-backend-m7o96jger
# A cleaner way to handle database connections.
# currently support psql, or mysql.

import psycopg2
import mysql.connector
import os
import datetime

class DBHelper:
    def __init__(self, choice):
        if choice == 'mysql': # default option
            self.conn = mysql.connector.connect(
                host=os.environ['MYSQL_HOST'],
                port=3306,
                user=os.environ['MYSQL_USER'],
                password=os.environ['MYSQL_PASSWORD'],
                database=os.environ['MYSQL_DATABASE'],
            )
            self.cur = self.conn.cursor(buffered=True)
        else: # psql - could be on Heroku? If not heroku, need to change the url parsing lines below
            DATABASE_URL = os.environ['DATABASE_URL']
            self.conn = psycopg2.connect(DATABASE_URL, sslmode='require')
            self.cur = self.conn.cursor()

    def setup(self):
        stmt = "CREATE TABLE IF NOT EXISTS pushid (id varchar(20), status varchar(5), eff_date datetime);"
        self.cur.execute(stmt)
        self.conn.commit()

    def add_user(self, user_chat_id):
        stmt = "INSERT INTO pushid (id,status,eff_date) VALUES (%s, %s, %s);"
        args = (user_chat_id, 'Y', datetime.datetime.now())
        self.cur.execute(stmt, args)
        self.conn.commit()

    def hard_delete_user(self, user_chat_id):
        stmt = "DELETE FROM pushid WHERE id = (%s);"
        args = (user_chat_id,)
        self.cur.execute(stmt, args)
        self.conn.commit()

    def soft_delete_user(self, user_chat_id):
        stmt = "UPDATE pushid SET status = 'N', eff_date = (%s) WHERE id = (%s) AND status = 'Y';"
        args = (datetime.datetime.now(), user_chat_id)
        self.cur.execute(stmt, args)
        self.conn.commit()

    def resurrect_user(self, user_chat_id):
        stmt = "UPDATE pushid SET status = 'Y', eff_date = (%s) WHERE id = (%s) AND status = 'N';"
        args = (datetime.datetime.now(), user_chat_id)
        self.cur.execute(stmt, args)
        self.conn.commit()

    def get_active_users(self):
        stmt = "SELECT id FROM pushid WHERE status = 'Y';"
        self.cur.execute(stmt)
        if self.cur.rowcount > 0:
            return [x[0] for x in self.cur.fetchall()]
        else:
            return []

    def get_all_users(self):
        stmt = "SELECT id FROM pushid;"
        self.cur.execute(stmt)
        if self.cur.rowcount > 0:
            return [x[0] for x in self.cur.fetchall()]
        else:
            return []

    def close_connection(self):
        self.cur.close()
        self.conn.close()