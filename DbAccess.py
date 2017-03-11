#!/usr/bin/env python

import time, sys, os, string
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

    def __init__(self, user, password, dbname):
        self.dbuser = user
        self.dbpassword = password
        self.dbname = dbname

        self.reconnect()

    def reconnect(self):
        retries = 5
        while True:
            try:
                self.db = MySQLdb.connect(host='localhost', user=self.dbuser, passwd=self.dbpassword, db=self.dbname)
                self.cur = self.db.cursor()
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
        
    def executeAndCommit(self, command, *args):
        retries = 3
        while retries > 0:
            try:
                status = self.cur.execute(command, args)
                self.db.commit()
                return status
            except MySQLdb.Error, e:
                try:
                    print "executeAndCommit(): MySQL Error [%d]: %s" % (e.args[0], e.args[1])
                except IndexError:
                    print "executeAndCommit(): MySQL Error: %s" % str(e)
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

    def executeAndFetchAll(self, command, *args):
        retries = 3
        while retries > 0:
            try:
                self.cur.execute(command, args)
                rows = self.cur.fetchall()
                return rows
            except MySQLdb.Error, e:
                try:
                    print "executeAndFetchAll(): MySQL Error [%d] on line %d: %s" % (e.args[0], sys.exc_info()[-1].tb_lineno, e.args[1])
                except IndexError:
                    print "executeAndFetchAll(): MySQL Error: %s" % str(e)
                if (e.args[0] == 2006):
                    self.reconnect()
                retries = retries - 1
                if (retries > 0):
                    print "Retrying..."
                else:
                    return

    def close(self):
        self.cur.close()
        self.db.close()
        
    def seen(self, nick):
        nick = string.replace(nick,"*","%")
        return self.executeAndFetchAll("SELECT * FROM seen WHERE name LIKE %s ORDER BY timestamp DESC LIMIT 3", MySQLdb.escape_string(nick))

    def updateSeen(self, nick, channel, message):
        rows = self.executeAndFetchAll("SELECT id FROM seen WHERE name = %s", nick)
        if rows:
            id = int(rows[0][0])
            self.executeAndCommit("UPDATE seen SET channel=%s, timestamp=NOW(), message=%s where id=%s", channel, message, id)
        else:
            self.executeAndCommit("INSERT INTO seen (name,channel,timestamp,message) VALUES (%s,%s,NOW(),%s)", nick, channel, message);

    def addFactoid(self, nick, item, are, value, replace):
        rows = self.executeAndFetchAll("SELECT id FROM factoids WHERE item=%s AND locked=1 LIMIT 1", item)
        if rows:
            print "Can't set factoid %s because it's locked." % item
            return False

        # If we're replacing, first delete all the existing rows
        if replace:
            self.forgetFactoid(item, nick)

        self.executeAndCommit("INSERT INTO factoids (item,are,value,nick,dateset) VALUES (%s,%s,%s,%s,NOW())", item,are,value,nick)
        self.executeAndCommit("INSERT INTO factoid_history (item,value,nick,dateset) VALUES (%s,%s,%s,NOW(6))", item,value,nick);
        return True

    def forgetFactoid(self, item, nick):
        rows = self.executeAndFetchAll("SELECT id FROM factoids WHERE item=%s AND locked=1 LIMIT 1", item);
        if rows:
            print "Can't forget factoid %s because it's locked." % item
            return False

        forgotten = False
        itemsDeleted = self.executeAndCommit("DELETE FROM factoids WHERE item=%s", item)
        if itemsDeleted > 0:
            forgotten = True
            self.executeAndCommit("INSERT INTO factoid_history (item,value,nick,dateset) VALUES (%s,Null,%s,NOW(6))", item,nick);
        return forgotten
        
    def getFactoid(self,item):
        rows = self.executeAndFetchAll("SELECT * FROM factoids WHERE item=%s ORDER BY dateset", item)
        if rows:
            key = int(rows[0][0])
            self.executeAndCommit("INSERT INTO refs (item, count, lastreferenced) VALUES(%s, 1, NOW()) ON DUPLICATE KEY UPDATE count=count+1", item);
        return rows

    def infoFactoid(self,item):
        return self.executeAndFetchAll("""SELECT * FROM factoid_history 
                                          LEFT JOIN refs ON factoid_history.item = refs.item
                                          WHERE factoid_history.item=%s 
                                          ORDER BY dateset DESC 
                                          LIMIT 4""", item)

    def addTell(self, author, recipient, message, inTracked):
        self.executeAndCommit("INSERT INTO tell (author, recipient, timestamp, message, inTracked) VALUES (%s,%s,NOW(),%s,%s)", author, recipient, message, inTracked);
        return True

    def getTell(self, recipient):
        rows = self.executeAndFetchAll("SELECT * FROM tell WHERE recipient=%s ORDER BY timestamp", recipient);
        if rows:
            self.executeAndCommit("DELETE FROM tell WHERE recipient=%s", recipient);
        return rows

    def addThingiverseRef(self, item):
        self.executeAndCommit("INSERT INTO thingiverseRefs (item, count, lastreferenced) VALUES(%s, 1, NOW()) ON DUPLICATE KEY UPDATE count=count+1", item);
        rows = self.executeAndFetchAll("SELECT count FROM thingiverseRefs WHERE item=%s", item);
        if rows:
            # First row, first item contains the result
            return int(rows[0][0])
        return 0

    def addYoutubeRef(self, item):
        self.executeAndCommit("INSERT INTO youtubeRefs (item, count, lastreferenced) VALUES(%s, 1, NOW()) ON DUPLICATE KEY UPDATE count=count+1", item);
        rows = self.executeAndFetchAll("SELECT count,title FROM youtubeRefs WHERE item=%s", item);
        return rows

    def addYoutubeTitle(self, item, title):
        self.executeAndCommit("UPDATE youtubeRefs SET title=%s where item=%s", title, item)

    def mood(self):
        rows = self.executeAndFetchAll("""SELECT botsnack - botsmack as mood
                                          FROM
                                          (
                                            SELECT IFNULL ((SELECT count FROM refs WHERE item="botsnack"), 0) as botsnack, botsmack
                                            FROM
                                            (
                                              SELECT IFNULL ((SELECT count FROM refs WHERE item="botsmack"), 0) as botsmack
                                            ) as T2
                                          ) as T;""")
        if not rows:
            return None
        else:
            return int(rows[0][0])

    # Test only methods    
    def deleteSeen(self, user):
        itemsDeleted = self.executeAndCommit("DELETE FROM seen WHERE name=%s", user)
        return itemsDeleted > 0

    def deleteAllFactoids(self):
        self.executeAndCommit("DELETE FROM factoids")
        self.executeAndCommit("DELETE FROM factoid_history")
        self.executeAndCommit("DELETE FROM refs")
                
    def lockFactoid(self, factoid):
        self.executeAndCommit("UPDATE factoids SET locked=1 where item=%s", factoid)

    def deleteAllTells(self):
        self.executeAndCommit("DELETE FROM tell")

    def deleteAllThingiverseRefs(self):
        self.executeAndCommit("DELETE FROM thingiverseRefs")

    def deleteAllYoutubeRefs(self):
        self.executeAndCommit("DELETE FROM youtubeRefs")
