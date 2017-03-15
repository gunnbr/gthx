#!/usr/bin/env python

"""
gthx - IRC bot as a backup for kthx

Responds for "seen", "tell", factoids

"""

# twisted imports
from twisted.words.protocols import irc
from twisted.internet import reactor, protocol, error
from twisted.python import log
from twisted.web.client import Agent
from twisted.web.http_headers import Headers
from twisted.protocols.basic import LineOnlyReceiver
from twisted.internet.defer import Deferred

# system imports
import time, sys, re, os
import traceback
import urllib

from datetime import datetime

from DbAccess import DbAccess
from DbAccess import Seen
from DbAccess import Tell

from Email import Email

from pprint import pprint

VERSION = "gthx version 0.23 2017-03-14"
trackednick = ""
channel = ""
mynick = ""


def unescape(htmlString):
    return htmlString.replace("&quot;","\"").replace("&gt;","<").replace("&lt;","<").replace("&apos;","'").replace("&amp;","&")

class TitleParser(LineOnlyReceiver):
        def __init__(self, finished):
            self.title = None
            self.finished = finished
            self.delimiter='\n'
            self.titleQuery = re.compile("<title>(.*) - .*<\/title>", re.IGNORECASE | re.MULTILINE)

        def lineReceived(self, line):
            if not line: return
            match = self.titleQuery.search(line)
            if match:
                self.title = match.group(1)
                print "Got title of: ", self.title
                self.loseConnection()
                
        def connectionLost(self, reason):
            print 'Finished receiving body:', reason.getErrorMessage()
            self.finished.callback(self.title)
            
def timesincestring(firsttime):
        since = datetime.now() - firsttime
        years = since.days / 365
        days = since.days % 365
        minutes = since.seconds / 60
        hours = minutes / 60
        minutes = minutes % 60
        seconds = since.seconds % 60
        sincestring = ""
        if years > 0:
            sincestring += "%s year" % years
            if years > 1:
                sincestring += "s"
            if days > 0 or hours > 0 or minutes > 0 or seconds > 0:
                sincestring += ", "
        if days > 0:
            sincestring += "%s day" % days
            if days > 1:
                sincestring += "s"
            if hours > 0 or minutes > 0 or seconds > 0:
                sincestring += ", "
        if hours > 0:
            sincestring += "%s hour" % hours
            if hours > 1:
                sincestring += "s"
            if minutes > 0 or seconds > 0:
                sincestring += ", "
        if minutes > 0:
            sincestring += "%s minute" % minutes
            if minutes > 1:
                sincestring += "s"
            if seconds > 0:
                sincestring += ", "
        if seconds > 0 or not sincestring:
            sincestring += "%s second" % seconds
            if seconds is not 1:
                sincestring += "s"
        return sincestring

class Gthx(irc.IRCClient):
    """An IRC bot for #reprap."""
    
    restring = ""

    def __init__(self):
        dbuser = os.getenv("GTHX_MYSQL_USER")
        if not dbuser:
            raise ValueError("No username specified. Have you set GTHX_MYSQL_USER?")

        dbpassword = os.getenv("GTHX_MYSQL_PASSWORD")
        if not dbpassword:
            raise ValueError("No password specified. Have you set GTHX_MYSQL_PASSWORD?")

        dbname = os.getenv("GTHX_MYSQL_DATABASE")
        if not dbname:
            raise ValueError("No database specified. Have you set GTHX_MYSQL_DATABASE?")

        self.db = DbAccess(dbuser, dbpassword, dbname)

        print "Connected to MySQL server"
        
        self.trackedpresent = dict()
        self.gotwhoischannel = False
        self.seenQuery = re.compile("\s*seen\s+([a-zA-Z\*_\\\[\]\{\}^`|\*][a-zA-Z0-9\*_\\\[\]\{\}^`|-]*)[\s\?]*")
        self.tellQuery = re.compile("\s*tell\s+([a-zA-Z\*_\\\[\]\{\}^`|\*][a-zA-Z0-9\*_\\\[\]\{\}^`|-]*)\s*(.+)")
        self.factoidQuery = re.compile("(.+)[?!](\s*$|\s*\|\s*([a-zA-Z\*_\\\[\]\{\}^`|\*][a-zA-Z0-9\*_\\\[\]\{\}^`|-]*)$)")
        self.factoidSet = re.compile("(.+?)\s(is|are)(\salso)?\s(.+)")
        self.googleQuery = re.compile("\s*google\s+(.*?)\s+for\s+([a-zA-Z\*_\\\[\]\{\}^`|\*][a-zA-Z0-9\*_\\\[\]\{\}^`|-]*)")
        self.thingMention = re.compile("http(s)?:\/\/www.thingiverse.com\/thing:(\d+)", re.IGNORECASE)
        self.youtubeMention = re.compile("http(s)?:\/\/www.youtube.com\/watch\?v=(\w*)", re.IGNORECASE)
        self.uptimeStart = datetime.now()
        self.lurkerReplyChannel = ""
        if os.getenv("GTHX_NICKSERV_PASSWORD"):
            self.log("Setting nickserv password")
            # Just setting this variable sets the nickserv login password
            self.password = os.getenv("GTHX_NICKSERV_PASSWORD")

    def connectionMade(self):
        if (self.password == None):
            self.log("IRC Connection made - no nickserv password")
        else:
            self.log("IRC Connection made -- sending CAP REQ")
            self.sendLine('CAP REQ :sasl')
        irc.IRCClient.connectionMade(self)

    def irc_CAP(self, prefix, params):
        self.log("Got irc_CAP")
        if params[1] != 'ACK' or params[2].split() != ['sasl']:
            print 'sasl not available'
            self.quit('')
        sasl = ('{0}\0{0}\0{1}'.format(self.nickname, self.password)).encode('base64').strip()
        self.sendLine('AUTHENTICATE PLAIN')
        self.sendLine('AUTHENTICATE ' + sasl)
  
    def irc_903(self, prefix, params):
        self.log("Got SASL connection successful.");
        self.sendLine('CAP END')
  
    def irc_904(self, prefix, params):
        print 'sasl auth failed', params
        self.quit('')

    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)
        self.log("[disconnected at %s]" % time.asctime(time.localtime(time.time())))
        self.emailClient.send("%s disconnected" % self.nickname, "%s is disconnected from the server.\n\n%s" % (self.nickname, reason))

    def log(self, message):
        """Write a message to the screen."""
        timestamp = time.strftime("[%H:%M:%S]", time.localtime(time.time()))
        print '%s %s' % (timestamp, message)

    # callbacks for events

    def signedOn(self):
        """Called when bot has succesfully signed on to server."""
        self.log("Signed on to the IRC server")
        self.channelList = [channel for channel in self.factory.channels.split(',')]
        for channelm in self.channelList:
            self.log("Joining channel %s" % channelm)
            self.join(channelm)
            if (trackednick == None):
                self.trackedpresent[channelm] = False

        self.gotwhoischannel = False
        # kthx uses: "\s*(${names})[:;,-]?\s*" to match nicks
        if (trackednick):
            self.matchNick = "(%s|%s)(:|;|,|-|\s)+(.+)" % (self.nickname, trackednick)
            print "Querying WHOIS %s at startup" % trackednick
            self.whois(trackednick)
        else:
            self.matchNick = "(%s)(:|;|,|-|\s)+(.+)" % (self.nickname)
            print "Running in standalone mode."

    def joined(self, channel):
        """Called when the bot joins the channel."""
        self.log("[I have joined %s as '%s']" % (channel, self.nickname))
        message = "I have joined channel %s as '%s'\n" % (channel, self.nickname)
        self.emailClient.threadsend("%s connected" % self.nickname, message)
        
    def userJoined(self, user, channel):
        """
        Called when I see another user joining a channel.
        """
        print "%s joined channel %s" % (user, channel)
        # TODO: Change this to verify the IP address before setting it
        if trackednick and (user == trackednick) and (self.trackedpresent[channel] == False):
            self.trackedpresent[channel] = True
            print "%s is here!" % trackednick
            self.emailClient.threadsend("%s status" % self.nickname, "%s has joined channel %s" % (user, channel))
                
            
    def userLeft(self, user, channel):
        """
        Called when I see another user leaving a channel.
        """
        print "%s left channel %s" % (user, channel)
        if trackednick and (user == trackednick) and (self.trackedpresent[channel]):
            self.trackedpresent[channel] = False
            print "%s is gone." % trackednick
            self.emailClient.threadsend("%s status" % self.nickname, "%s has left channel %s" % (user, channel))

    def userQuit(self, user, quitMessage):
        """
        Called when I see another user disconnect from the network.
        """
        safeQuitMessage = quitMessage.decode("utf-8")
        print "%s disconnected : %s" % (user, safeQuitMessage)
        if trackednick and (user == trackednick):
            for channel in self.channelList:
                self.trackedpresent[channel] = False
            print "%s is gone." % trackednick
            self.emailClient.threadsend("%s status" % self.nickname, "%s has quit: %s" % (user, quitMessage))

    def userKicked(self, kickee, channel, kicker, message):
        """
        Called when I observe someone else being kicked from a channel.
        """
        print "In %s, %s kicked %s : %s" % (channel, kicker, kickee, message)
        if trackednick and (kickee == trackednick) and (self.trackedpresent[channel]):
            self.trackedpresent[channel] = False
            print "%s is gone." % trackednick
            self.emailClient.threadsend("%s status" % self.nickname, "%s has been kicked from %s by %s: %s" % (kickee, channel, kicker, message))

    def userRenamed(self, oldname, newname):
        """
        A user changed their name from oldname to newname.
        """
        print "%s renamed to %s" % (oldname, newname)
        if (trackednick == None):
            return
        if oldname == trackednick:
            for channel in self.channelList:
                self.trackedpresent[channel] = False
            print "%s is gone." % trackednick
            self.emailClient.threadsend("%s status" % self.nickname, "%s has been renamed to %s" % (oldname, newname))
        if newname == trackednick:
            self.whois(trackednick)
            print "%s is here!" % trackednick
            self.emailClient.threadsend("%s status" % self.nickname, "%s has been renamed to %s--checking WHOIS" % (oldname, newname))

    def irc_unknown(self, prefix, command, params):
        print "Unknown command '%s' '%s' '%s'" % (prefix, command, params)
        if (command == 'RPL_NAMREPLY'):
            if (self.lurkerReplyChannel == ""):
                return
            users = params[3].split()
            for user in users:
                self.channelCount = self.channelCount + 1
                rows = self.db.seen(user)
                if len(rows) == 0:
                       self.lurkerCount = self.lurkerCount + 1
        elif (command == 'RPL_ENDOFNAMES'):
            if (self.lurkerReplyChannel == ""):
                return
            print "Got RPL_ENDOFNAMES"
            self.msg(self.lurkerReplyChannel,"%d of the %d users in %s right now have never said anything." % (self.lurkerCount, self.channelCount, params[1]))
            self.lurkerReplyChannel = ""

    def irc_RPL_WHOISCHANNELS(self, prefix, params):
        """This method is called when the client recieves a reply for whois.
        params[0]: requestor
        params[1]: nick requested
        params[2]: list of channels in common
        """
        print "Got WHOISCHANNELS with prefix '%s' and params '%s'" % (prefix, params)
        print "%s is in channels %s" % (params[1], params[2])
        self.gotwhoischannel = True
        trackedchannels = params[2].translate(None, '@').split(" ")
        for channel in self.channelList:
            if channel in trackedchannels:
                self.trackedpresent[channel] = True
                print "%s is in %s!!" %  (params[1], channel)
                self.emailClient.threadsend("%s status" % self.nickname, "%s is in channel %s" % (params[1], params[2]))
            else:
                self.trackedpresent[channel] = False
                print "%s is NOT in %s!!" %  (params[1], channel)

    def irc_RPL_WHOISUSER(self, prefix, params):
        print "Got WHOISUSER with prefix '%s' and params '%s'" % (prefix, params)

    def irc_RPL_WHOISSERVER(self, prefix, params):
        print "Got WHOISSERVER with prefix '%s' and params '%s'" % (prefix, params)

    def irc_RPL_WHOISOPERATOR(self, prefix, params):
        print "Got WHOISOPERATOR with prefix '%s' and params '%s'" % (prefix, params)

    def irc_RPL_WHOISIDLE(self, prefix, params):
        print "Got WHOISIDLE with prefix '%s' and params '%s'" % (prefix, params)

    def irc_RPL_ENDOFWHOIS(self, prefix, params):
        print "Got ENDOFWHOIS with prefix '%s' and params '%s'" % (prefix, params)
        if not self.gotwhoischannel:
            if (trackednick != None):
                print "No response from %s. Must not be present." % trackednick
                for channel in self.channelList:
                    self.trackedpresent[channel] = False
                    self.emailClient.threadsend("%s status" % self.nickname, "%s is not in channel %s" % (trackednick, channel))

    def getFactoidString(self, query):
        answer = self.db.getFactoid(query)
        if answer:
            for i, factoid in enumerate(answer):
                if i == 0:
                    if factoid[3].startswith("<reply>") or factoid[3].startswith("<action>"):
                        fstring = factoid[3]
                        break
                    else:
                        fstring = query
                fstring += "%s" % " are " if factoid[2] else " is "
                if i > 0:
                    fstring += "also "
                fstring += factoid[3]
                if i < len(answer) - 1:
                    fstring += " and"
            return fstring
        else:
            return None

    def moodToString(self, mood):
        if mood < -100:
            return "suicidal!"
        if mood < -50:
            return "really depressed."
        if mood < -10:
            return "depressed."
        if mood < 0:
            return "kinda bummed."
        if mood == 0:
            return "meh, okay I guess."
        if mood < 10:
            return "alright."
        if mood < 50:
            return "pretty good."
        return "great, Great, GREAT!!"

    def privmsg(self, user, channel, msg):
        """Called when the bot receives a message, both public and private."""
        user = user.split('!', 1)[0]

        # By default, don't reply to anything
        canReply = False
        private = False
        replyChannel = channel
        parseMsg = msg
        directAddress = False

        # Debug print ALL messages
        #print "Message from '%s' on '%s': '%s'" % (user, channel, msg)
        
        # Check to see if they're sending me a private message
        if channel == self.nickname:
            canReply = True
            private = True
            replyChannel = user
            self.log("Private message from %s: %s" % (user, msg))
            if str.lower(user) == "nickserv":
                self.log("Nickserv says: %s" % msg)
            if parseMsg.startswith("whois "):
                whoisnick = parseMsg.split(" ",1)[1]
                print "Doing a whois '%s'" % whoisnick
                self.whois(whoisnick)

        # Update the seen database, but only if it's not a private message
        if channel in self.channelList and not private:
            self.db.updateSeen(user,channel,msg)

        # If kthx said something, mark him as here and ignore everything he says
        if user == trackednick and not private:
            if (self.trackedpresent[channel] == False):
                self.trackedpresent[channel] = True
                self.emailClient.threadsend("%s status" % self.nickname, "%s spoke in %s unexpectedly and got marked as present: %s" % (user, channel,msg))
            return
        
        # If kthx is gone, then we can always reply
        if not private and not self.trackedpresent[channel]:
            canReply = True

        # Check to see if we have a tell waiting for this user
        tells = self.db.getTell(user)
        if tells:
            for message in tells:
                print "Found tell for '%s' from '%s'" % (user, message[Tell.author])
                author = message[Tell.author]
                timestring = timesincestring(message[Tell.timestamp])
                text = message[Tell.message]
                inTracked = message[Tell.inTracked]
                # We have 3 cases:
                # 1) kthx was around when this tell happened and is still around now.
                #    In this case, we assume kthx will relay the message and just delete it
                # 2) kthx was around when this tell happened and is not here now.
                #    In this case, we want to send the message and mention that kthx may repeat it
                # 3) kthx was not around when this tell happened and may or may not be here now
                #    Whether or not kthx is now here, we need to say the message
                # 4) gthx was specifically addressed for this tell
                #    Whether or not kthx is now here, we need to say the message
                #
                # If we can't reply, it means that kthx is present. In that
                # case, the tell has already been erased, so in both cases,
                # we're good.
                if canReply or not inTracked:
                    if inTracked:
                        self.msg(replyChannel,"%s: %s ago <%s> tell %s %s (%s may repeat this)" % (user, timestring, author, user, text, trackednick))
                    else:
                        self.msg(replyChannel,"%s: %s ago <%s> tell %s %s" % (user, timestring, author, user, text))

        # Check for specifically addressed messages
        m = re.match(self.matchNick, parseMsg)
        if m:
            print "Found message addressed to '%s'. My nick is '%s'." % (m.group(1), self.nickname)
            parseMsg = m.group(3)
            # Mark it as a direct address so we can look for a factoid
            directAddress = True
            # If it's addressed directly to me, we can reply
            if m.group(1) == self.nickname:
                canReply = True
            
        # Check for status query
        if canReply and parseMsg == "status?":
            if (trackednick):
                if (private):
                    reply = "%s: OK; Up for %s; " % (VERSION, timesincestring(self.uptimeStart))
                    for channel in self.channelList:
                        reply += "%s %s; " % (channel, "PRESENT" if self.trackedpresent[channel] else "GONE")
                else:
                    reply = "%s: OK; Up for %s; %s is %s" % (VERSION, timesincestring(self.uptimeStart), trackednick, "PRESENT" if self.trackedpresent[channel] else "GONE")
            else:
                reply = "%s: OK; Up for %s; standalone mode" % (VERSION, timesincestring(self.uptimeStart))
            mood = self.db.mood()
            reply += " mood: %s" % self.moodToString(mood)
            self.msg(replyChannel, reply)
            return
        
        # Check for lurker query
        if canReply and parseMsg == "lurkers?":
            self.msg(replyChannel, "Looking for lurkers...")
            self.lurkerReplyChannel = replyChannel
            self.lurkerCount = 0
            self.channelCount = 0
            print "Sending request 'NAMES %s'" % channel
            self.sendLine("NAMES %s" % channel)
            return
        
        # Check for tell query
        m = self.tellQuery.match(parseMsg)
        if m and directAddress:
            print "Got tell from '%s' for  '%s' message '%s'." % (user, m.group(1), m.group(2))
            # The is in the tracked bot if the tracked bot is present and it was not a message 
            # specifically directed to us. This is a little tricky since the only way to know
            # that a message was specifically directed to us is to see if it was a direct address
            # and we can reply
            success = self.db.addTell(user, m.group(1), m.group(2), not (directAddress and canReply) and self.trackedpresent[channel])
            if success and canReply:
                self.msg(replyChannel, "%s: I'll pass that on when %s is around." % (user, m.group(1)))
            return
        
        # Check for seen query
        if canReply:
            m = self.seenQuery.match(parseMsg)
            if m:
                queryname = m.group(1)
                print "%s asked about '%s'" % (user, queryname)
                rows = self.db.seen(queryname)
                if len(rows) == 0:
                    reply = "Sorry, I haven't seen %s." % queryname
                    self.msg(replyChannel, reply)
                for i,row in enumerate(rows):
                    reply = "%s was last seen in %s %s ago saying '%s'." % (row[Seen.name], row[Seen.channel], timesincestring(row[Seen.timestamp]), row[Seen.message])
                    self.msg(replyChannel, reply)
                    if i >= 2:
                        # Don't reply more than 3 times to a seen query
                        break
                return
        
        # Check for google query
        if canReply:
            m = self.googleQuery.match(parseMsg)
            if m:
                queryname = urllib.quote_plus(m.group(1))
                foruser = m.group(2)
                print "%s asked to google '%s' for %s" % (user, queryname, foruser)
                reply = "%s: http://lmgtfy.com/?q=%s" % (foruser, queryname)
                self.msg(replyChannel, reply)
                return
        
        # Check for setting a factoid
        factoid = None
        if directAddress:
            factoid = self.factoidSet.match(parseMsg)
            if factoid:
                invalidwords = re.match('(here|how|it|something|that|this|what|when|where|which|who|why|you)', factoid.group(1), re.IGNORECASE)
                if not invalidwords:
                    safeFactoid = factoid.group(1).decode("utf-8")
                    print "%s tried to set factoid '%s'." % (user, safeFactoid)
                    success = self.db.addFactoid(user, factoid.group(1), True if factoid.group(2) == 'are' else False, factoid.group(4), True if not factoid.group(3) else False)
                    if canReply:
                        if success:
                            self.msg(replyChannel, "%s: Okay." % user)
                        else:
                            self.msg(replyChannel, "I'm sorry, %s. I'm afraid I can't do that." % user)

        # Check for getting a factoid
        if canReply:
            f = self.factoidQuery.match(parseMsg)
            if f:
                safeFactoid = f.group(1).decode("utf-8")
                print "factoid query from %s:%s for '%s'" % (user, channel, safeFactoid)
                answer = self.getFactoidString(f.group(1))
                if answer:
                    # Replace !who and !channel in the reply
                    answer = re.sub("!who", user, answer)
                    answer = re.sub("!channel", channel, answer)
                
                    if answer.startswith("<reply>"):
                        answer = answer[7:]

                    if answer.startswith("<action>"):
                        self.describe(replyChannel, answer[8:])
                    else:
                        if (f.group(3)):
                            answer = "%s, %s" % (f.group(3), answer)
                        self.msg(replyChannel, answer)

        # Check for info request
        if canReply and parseMsg.startswith("info "):
            query = parseMsg[5:]
            if query[-1:] == "?":
                query = query[:-1]
            safeFactoid = query.decode("utf-8")
            print "info request for '%s' ReplyChannel is '%s'" % (safeFactoid, replyChannel)
            refcount = 0
            answer = self.db.infoFactoid(query)
            if answer:
                count = answer[0][6]
                if not count:
                    count = "0"
                print "Factoid '%s' has been referenced %s times" % (safeFactoid, count)
                self.msg(replyChannel, "Factoid '%s' has been referenced %s times" % (query, count))
                for factoid in answer:
                    user = factoid[3]
                    value = factoid[2]
                    if not user:
                        user = "Unknown"
                    if value:
                        safeValue = value.decode("utf-8")
                        print "At %s, %s set to: %s" % (factoid[4], user, safeValue)
                        self.msg(replyChannel, "At %s, %s set to: %s" % (factoid[4], user, value))
                    else:
                        print "At %s, %s deleted this item" % (factoid[4], user)
                        self.msg(replyChannel, "At %s, %s deleted this item" % (factoid[4], user))
            else:
                print "No info for factoid '%s'" % safeFactoid
                self.msg(replyChannel, "Sorry, I couldn't find an entry for %s" % query)

        # Check for forget request
        if directAddress and parseMsg.startswith("forget "):
            query = parseMsg[7:]
            print "forget request for '%s'" % query
            forgotten = self.db.forgetFactoid(query, user)
            if canReply:
                if forgotten:
                    self.msg(replyChannel, "%s: I've forgotten about %s" % (user, query))
                else:
                    self.msg(replyChannel, "%s: Okay, but %s didn't exist anyway" % (user, query))

        # Check for thingiverse mention
        if canReply:
            match = self.thingMention.search(parseMsg)
            if match:
                thingId = int(match.group(2))
                print "Match for thingiverse query item %s" % thingId
                rows = self.db.addThingiverseRef(thingId)
                refs = int(rows[0][0])
                title = rows[0][1]
                if title is None:
                    print "Attemping to get title for thingiverse ID %s" % thingId
                    agent = Agent(reactor)
                    titleQuery = agent.request(
                        'GET',
                        'http://www.thingiverse.com/thing:%s' % thingId,
                        Headers({'User-Agent': ['gthx IRC bot']}),
                        None)
                    def titleResponse(title):
                        if title:
                            title = unescape(title)
                            self.db.addThingiverseTitle(thingId, title)
                            print "The title for thing %s is: %s " % (thingId, title)
                            reply = 'http://www.thingiverse.com/thing:%s => %s => %s IRC mentions' % (thingId, title, refs)
                            self.msg(replyChannel, reply)
                        else:
                            print "No title found for thing %s" % (thingId)
                            reply = 'http://www.thingiverse.com/thing:%s => ???? => %s IRC mentions' % (thingId, refs)
                            self.msg(replyChannel, reply)
                    
                    def queryResponse(response):
                        if response.code == 200:
                            finished = Deferred()
                            finished.addCallback(titleResponse)
                            response.deliverBody(TitleParser(finished))
                            return finished
                        print "Got error response from thingiverse query: %s" % (response)
                        titleResponse(None)
                        return None
            
                    titleQuery.addCallback(queryResponse)
                else:
                    print "Already have a title for thing %s: %s" % (thingId, title)
                    reply = 'http://www.thingiverse.com/thing:%s => %s => %s IRC mentions' % (thingId, title, refs)
                    self.msg(replyChannel, reply)

        # Check for youtube mention
        if canReply:
            match = self.youtubeMention.search(parseMsg)
            if match:
                youtubeId = match.group(2)
                print "Match for youtube query item %s" % youtubeId
                rows = self.db.addYoutubeRef(youtubeId)
                refs = int(rows[0][0])
                title = rows[0][1]
                if title is None:
                    print "Attemping to get title for youtubeId %s" % youtubeId
                    agent = Agent(reactor)
                    titleQuery = agent.request(
                        'GET',
                        'https://www.youtube.com/watch?v=%s' % youtubeId,
                        Headers({'User-Agent': ['gthx IRC bot']}),
                        None)
                    def titleResponse(title):
                        if title:
                            title = unescape(title)
                            self.db.addYoutubeTitle(youtubeId, title)
                            print "The title for video %s is: %s " % (youtubeId, title)
                            reply = 'http://www.youtube.com/watch?v=%s => %s => %s IRC mentions' % (youtubeId, title, refs)
                            print "Reply is: %s" % reply
                            self.msg(replyChannel, reply)
                            print "Message sent."
                        else:
                            print "No title found for youtube video %s" % (youtubeId)
                            reply = 'http://www.youtube.com/watch?v=%s => ???? => %s IRC mentions' % (youtubeId, refs)
                            self.msg(replyChannel, reply)
                    
                    def queryResponse(response):
                        if response.code == 200:
                            finished = Deferred()
                            finished.addCallback(titleResponse)
                            response.deliverBody(TitleParser(finished))
                            return finished
                        print "Got error response from youtube query: %s:%s" % (response.code, response.phrase)
                        pprint(list(response.headers.getAllRawHeaders()))
                        titleResponse(None)
                        return None
            
                    titleQuery.addCallback(queryResponse)
                else:
                    print "Already have a title for item %s: %s" % (youtubeId, title)
                    reply = 'http://www.youtube.com/watch?v=:%s => %s => %s IRC mentions' % (youtubeId, title, refs)
                    self.msg(replyChannel, reply)
                
    def action(self, sender, channel, message):
        m = re.match("([a-zA-Z\*_\\\[\]\{\}^`|\*][a-zA-Z0-9\*_\\\[\]\{\}^`|-]*)", sender)
        if m:
            sender = m.group(1)
            print "* %s %s" % (sender, message)
            self.db.updateSeen(sender, channel, "* %s %s" % (sender, message))
            
class GthxFactory(protocol.ClientFactory):
    """A factory for Gthx.

    A new protocol instance will be created each time we connect to the server.
    """

    def __init__(self, channels, nick, emailClient):
        self.channels = channels
        self.emailClient = emailClient
        self.nick = nick
        print "GthxFactory init"
        
    def buildProtocol(self, addr):
        print "GthxFactory build protocol"
        try:
            p = Gthx()
            p.factory = self
            p.emailClient = self.emailClient
            p.nickname = self.nick
            return p
        except Exception as e:
            print "Failed to create Gthx instance: %s" % str(e)
            print "Traceback: %s" % traceback.format_exc()
            # TODO: Figure out how to handle the error and exit here
            raise

    def clientConnectionLost(self, connector, reason):
        """If we get disconnected, reconnect to server."""
        print "GthxFactory client connection"
        # TODO: Send email notification
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print "connection failed:", reason
        # TODO: Send email notification
        reactor.stop()


if __name__ == '__main__':
    trackednick = os.getenv("GTHX_TRACKED_NICK")
    channels = os.getenv("GTHX_CHANNELS")
    mynick = os.getenv("GTHX_NICK")
    
    logfile = "/tmp/%s.log" % mynick

    if (channels == None):
        print "No channel specified. Did you set GTHX_CHANNELS?"
    elif (mynick == None):
        print "No nick specified. Did you set GTHX_NICK?"
    else:
        try:
            # Setup email notification
            emailClient = Email()

            # initialize logging
            log.startLogging(open(logfile, 'a'))

            # create factory protocol and application
            f = GthxFactory(channels, mynick, emailClient)

            # connect factory to this host and port
            reactor.connectTCP("chat.freenode.net", 6667, f)

            # run bot
            reactor.run()
        except ValueError as e:
            print "Failed to start: %s" % e
        except error.ReactorNotRestartable as e:
            print "Got severe failure--probably ^C. Exiting"
            emailClient.send("%s exiting" % mynick, "%s is exiting due to a user requested shutdown." % mynick)
            # TODO: Figure out a way to gracefully shutdown and close the DB connection
        except Exception as e:
            print "Overall failure: %s" % str(e)
            print "Traceback: %s" % traceback.format_exc()
            message = "%s stopped due to an exception: %s\n\n" % (mynick, str(e))
            message += traceback.format_exc()
            emailClient.send("%s exception" % mynick, message)
            print "Waiting 5 minutes to retry..."
            # TODO: Add logging here
