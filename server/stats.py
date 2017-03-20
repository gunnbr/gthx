#!/usr/bin/env python

import MySQLdb as mdb
import cgi
import json
import ConfigParser
import datetime
import sys

debug = False

form = cgi.FieldStorage()

reply = {}

con = None

try:
    print "Content-Type: text/json"
    print

    try:
        reply['id'] = form['id'].value
    except KeyError:
        pass
    
    try:
        type = form['type'].value
    except KeyError:
        type = "factoids"

    if type not in ['factoids', 'thingiverse', 'youtube']:
        raise ValueError("Invalid type '%s'" % type)
    
    try:
        range = form['range'].value
    except KeyError:
        range = "all"

    if range not in ['recent', 'all']:
        raise ValueError("Invalid range '%s'" % range)
    
    try:
        order = form['order'].value
    except KeyError:
        order = "count"

    if order not in ['date', 'count']:
        raise ValueError("Invalid order '%s'" % order)

    try:
        test = form['debug']
        print "DEBUG MODE ENABLED"
        debug = True
    except KeyError:
        pass

    if debug:
        configFile = '../gthx.config.local'
    else:
        configFile = '/etc/gthx/gthx.config'

    config = ConfigParser.ConfigParser()
    results = config.read(configFile)
    if not results:
        if debug:
            error = "Failed to read config file '%s'" % (configFile)
        else:
            error = "Not configured"
        raise mdb.Error(500, error)

    dbUser = config.get('MYSQL','GTHX_MYSQL_USER')
    dbPassword = config.get('MYSQL','GTHX_MYSQL_PASSWORD')
    dbDatabase = config.get('MYSQL','GTHX_MYSQL_DATABASE')
    
    # connect to the database
    con = mdb.connect("localhost", dbUser, dbPassword, dbDatabase)

    cur = con.cursor(mdb.cursors.DictCursor)

    if type == 'factoids':
        query = "SELECT * FROM refs WHERE item NOT IN (\"botsnack\",\"botsmack\") "
    elif type == 'thingiverse':
        query = "SELECT * FROM thingiverseRefs "
    else:
        query = "SELECT * from youtubeRefs "
        
    if range == 'recent':
        if type == 'factoids':
            query += "AND "
        else:
            query += "WHERE "
        query += "lastreferenced BETWEEN DATE_SUB(NOW(), INTERVAL 30 DAY) AND NOW() "

    if order == 'date':
        query += "ORDER BY lastreferenced desc "
    else:
        query += "ORDER BY count desc, lastreferenced desc "
        
    query += "LIMIT 20"

    cur.execute(query)

    rows = cur.fetchall()

    reply["data"] = []
    
    for row in rows:
        reply["data"].append(row)

    reply["status"] = "success"

except mdb.Error, e:
    reply["status"] = "failure"
    reply["reason"] = e.args[1]
except ValueError, e:
    reply["status"] = "failure"
    reply["reason"] = e.args[0]
    

if con:
    con.close()

def DatetimeHandler(obj):
        """JSON serializer for objects not serializable by default json code"""
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        raise TypeError("Type not serializable")
    
if debug:
    print json.dumps(reply, default=DatetimeHandler, sort_keys=True, indent=4, separators=(',', ': '))
else:                                                
    print json.dumps(reply, default=DatetimeHandler, separators=(',',':'))
                    
