#!/usr/bin/env python

import time, sys, os, datetime, string
import MySQLdb

class Seen:
    id = 0
    name = 1
    channel = 2
    timestamp = 3
    message = 4

class Tell:
    id = 0
    author = 1
    recipient = 2
    timestamp = 3
    message = 4
    inTracked = 5

class DbAccess():
    """Database Access

    Gives access to read and write all the tables in the database
    """

    def __init__(self):
        self.dbuser = os.getenv("GTHX_MYSQL_USER")
        if (self.dbuser == None):
            raise ValueError("No username specified. Have you set GTHX_MYSQL_USER?")

        self.dbpassword = os.getenv("GTHX_MYSQL_PASSWORD")
        if (self.dbpassword == None):
            raise ValueError("No password specified. Have you set GTHX_MYSQL_PASSWORD?")

        self.database = os.getenv("GTHX_MYSQL_DATABASE")
        if (self.database == None):
            raise ValueError("No database specified. Have you set GTHX_MYSQL_DATABASE?")

        self.reconnect()

    def reconnect(self):
        retries = 5
        while True:
            try:
                self.db = MySQLdb.connect(host='localhost', user=self.dbuser, passwd=self.dbpassword, db=self.database)
                self.cur = self.db.cursor()
                print "Connected to MySQL server"
                return
            except MySQLdb.Error, e:
                try:
                    print "Failed to connect. MySQL Error [%d]: %s" % (e.args[0], e.args[1])
                    retries = retries - 1
                    if (retries > 0):
                        print "Waiting to retry (%d)" % retries
                        time.sleep(30)
                    else:
                        raise e
                except IndexError:
                    print "MySQL Error: %s" % str(e)
                    raise e
        
    def seen(self, nick):
        retries = 3
        while True:
            try:
                nick = string.replace(nick,"*","%")
                self.cur.execute("SELECT * FROM seen WHERE name LIKE %s ORDER BY timestamp DESC LIMIT 3", (nick,));
                rows = self.cur.fetchall()
                return rows
            except MySQLdb.Error, e:
                try:
                    print "seen(): MySQL Error [%d] on line %d: %s" % (e.args[0], sys.exc_info()[-1].tb_lineno, e.args[1])
                except IndexError:
                    print "seen(): MySQL Error: %s" % str(e)
                if (e.args[0] == 2006):
                    self.reconnect()
                retries = retries - 1
                if (retries > 0):
                    print "Retrying..."
                else:
                    return

    def updateSeen(self, nick, channel, message):
        retries = 3
        while True:
            try:
                self.cur.execute("SELECT id FROM seen WHERE name = %s", (nick,));
                time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                if (self.cur.rowcount > 0):
                    id = self.cur.fetchone()[0]
                    self.cur.execute("UPDATE seen SET channel='%s', timestamp='%s', message='%s' where id='%s'", (channel, time, message, id))
                else:
                    self.cur.execute("INSERT INTO seen (name,channel,timestamp,message) VALUES (%s,%s,%s,%s)", (nick, channel, time, message));
                self.db.commit()
                return
            except MySQLdb.Error, e:
                try:
                    print "updateSeen(): MySQL Error [%d] on line %d: %s" % (e.args[0], sys.exc_info()[-1].tb_lineno, e.args[1])
                except IndexError:
                    print "updateSeen(): MySQL Error: %s" % str(e)

                if (e.args[0] == 2006):
                    print "Reconnecting..."
                    self.reconnect()
                else:
                    try:
                        print "Rolling back..."
                        self.db.rollback()
                    except MySQLdb.Error:
                        print "Rollback failed."

                retries = retries - 1
                if (retries > 0):
                    print "Retrying..."
                else:
                    return

    def addFactoid(self, nick, item, are, value, replace):
        retries = 3
        while True:
            try:
                self.cur.execute("SELECT id FROM factoids WHERE item=%s AND locked=1 LIMIT 1", (item,));
                rows = self.cur.fetchall()
                if rows:
                    print "Can't set factoid %s because it's locked." % item
                    return False

                # If we're replacing, first delete all the existing rows
                if replace:
                    self.forgetFactoid(item, nick)
                time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.cur.execute("INSERT INTO factoids (item,are,value,nick,dateset) VALUES (%s,%s,%s,%s,%s)", (item,are,value,nick,time));
                self.db.commit()
                return True
            except MySQLdb.Error, e:
                try:
                    print "addFactoid(): MySQL Error [%d]: %s" % (e.args[0], e.args[1])
                except IndexError:
                    print "addFactoid(): MySQL Error: %s" % str(e)
                if (e.args[0] == 2006):
                    self.reconnect()
                else:
                    try:
                        print "Rolling back..."
                        self.db.rollback()
                    except MySQLdb.Error:
                        print "Rollback failed."
                        
                retries = retries - 1
                if (retries > 0):
                    print "Retrying..."
                else:
                    return False

    def forgetFactoid(self, item, nick):
        retries = 3
        while True:
            try:
                self.cur.execute("SELECT id FROM factoids WHERE item=%s AND locked=1 LIMIT 1", (item,));
                rows = self.cur.fetchall()
                if rows:
                    print "Can't forget factoid %s because it's locked." % item
                    return False

                forgotten = False
                itemsDeleted = self.cur.execute("DELETE FROM factoids WHERE item=%s", (item,))
                if itemsDeleted > 0:
                    forgotten = True
                    time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    self.cur.execute("INSERT INTO factoid_history (item,value,nick,dateset) VALUES (%s,Null,%s,%s)", (item,nick,time));
                self.db.commit()
                return forgotten
            except MySQLdb.Error, e:
                try:
                    print "forgetFactoid(): MySQL Error [%d]: %s" % (e.args[0], e.args[1])
                except IndexError:
                    print "forgetFactoid(): MySQL Error: %s" % str(e)
                if (e.args[0] == 2006):
                    self.reconnect()
                else:
                    try:
                        print "Rolling back..."
                        self.db.rollback()
                    except MySQLdb.Error:
                        print "Rollback failed."
                    
                retries = retries - 1
                if (retries > 0):
                    print "Retrying..."
                else:
                    return None
        
    def getFactoid(self,item):
        retries = 3
        while True:
            try:
                self.cur.execute("SELECT * FROM factoids WHERE item=%s ORDER BY dateset", (item,));
                rows = self.cur.fetchall()
                return rows
            except MySQLdb.Error, e:
                try:
                    print "getFactoid(): MySQL Error [%d]: %s" % (e.args[0], e.args[1])
                except IndexError:
                    print "getFactoid(): MySQL Error: %s" % str(e)
                if (e.args[0] == 2006):
                    self.reconnect()
                retries = retries - 1
                if (retries > 0):
                    print "Retrying..."
                else:
                    return None

    def infoFactoid(self,item):
        retries = 3
        while True:
            try:
                self.cur.execute("SELECT * FROM factoid_history WHERE item=%s ORDER BY dateset DESC LIMIT 4", (item,));
                rows = self.cur.fetchall()
                return rows
            except MySQLdb.Error, e:
                try:
                    print "infoFactoid(): MySQL Error [%d]: %s" % (e.args[0], e.args[1])
                except IndexError:
                    print "infoFactoid(): MySQL Error: %s" % str(e)
                if (e.args[0] == 2006):
                    self.reconnect()
                retries = retries - 1
                if (retries > 0):
                    print "Retrying..."
                else:
                    return None

    def addTell(self, author, recipient, message, inTracked):
        retries = 3
        while True:
            try:
                time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.cur.execute("INSERT INTO tell (author, recipient, timestamp, message, inTracked) VALUES (%s,%s,%s,%s,%s)", (author, recipient, time, message, inTracked));
                self.db.commit()
                return True
            except MySQLdb.Error, e:
                try:
                    print "addTell(): MySQL Error [%d]: %s" % (e.args[0], e.args[1])
                except IndexError:
                    print "addTell(): MySQL Error: %s" % str(e)
                if (e.args[0] == 2006):
                    self.reconnect()
                else:
                    try:
                        print "Rolling back..."
                        self.db.rollback()
                    except MySQLdb.Error:
                        print "Rollback failed."
                    
                retries = retries - 1
                if (retries > 0):
                    print "Retrying..."
                else:
                    return False

    def getTell(self,recipient):
        retries = 3
        while True:
            try:
                self.cur.execute("SELECT * FROM tell WHERE recipient=%s ORDER BY timestamp", (recipient,));
                rows = self.cur.fetchall()
                if rows:
                    self.cur.execute("DELETE FROM tell WHERE recipient=%s", (recipient,));
                    self.db.commit()
                return rows
            except MySQLdb.Error, e:
                try:
                    print "getTell(): MySQL Error [%d]: %s" % (e.args[0], e.args[1])
                except IndexError:
                    print "getTell(): MySQL Error: %s" % str(e)
                if (e.args[0] == 2006):
                    self.reconnect()
                else:
                    try:
                        print "Rolling back..."
                        self.db.rollback()
                    except MySQLdb.Error:
                        print "Rollback failed."
                retries = retries - 1
                if (retries > 0):
                    print "Retrying..."
                else:
                    return None
        
    def close(self):
        self.cur.close()
        self.db.close()
        
    
