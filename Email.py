#!/usr/bin/env python

import sys, os, thread
import smtplib

class Email():
    """Email support

    Provides methods to send email for notifications
    """

    def __init__(self, user, password, from_email, to_email, server):
        self.user = user
        self.password = password
        self.from_email = from_email
        self.to_email = to_email
        self.server = server

    def threadsend(self, subject, message):
        try:
            thread.start_new_thread(self.send, (subject, message))
        except Exception as e:
            print "Failed to start a thread email: %s" % e
        
    def send(self, subject, message):
        if ((self.user != None) and (self.password != None) and (self.server != None)):
            print "Sending email notification..."

            # Create a text/plain message
            msg = "To: %s\n" % self.to_email
            msg += "From: %s\n" % self.from_email
            msg += "Subject: %s\n\n" % subject
            msg += message

            # Now send the message
            try:
                #s = smtplib.SMTP(self.server)
                s = smtplib.SMTP_SSL(self.server)
                s.set_debuglevel(True)
                # Only use starttls() with SMTP, not SMTP_SSL
                #s.starttls()
                s.login(self.user, self.password)
                s.sendmail(self.from_email, [self.to_email], msg)
                s.quit()
            except Exception as e:
                print "Failed to send email notification: %s" % e
            
            print "Done with email"

