#!/usr/bin/env python

import sys, os, thread
import smtplib

class Email():
    """Email support

    Provides methods to send email for notifications
    """

    def __init__(self):
        self.user = os.getenv("GTHX_EMAIL_USER")
        if (self.user == None):
            raise ValueError("No email username specified. Have you set GTHX_EMAIL_USER?")

        self.password = os.getenv("GTHX_EMAIL_PASSWORD")
        if (self.password == None):
            raise ValueError("No email password specified. Have you set GTHX_EMAIL_PASSWORD?")

        self.from_email = os.getenv("GTHX_EMAIL_FROM")
        if (self.from_email == None):
            raise ValueError("No email from specified. Have you set GTHX_EMAIL_FROM?")

        self.to_email = os.getenv("GTHX_EMAIL_TO")
        if (self.to_email == None):
            raise ValueError("No email to specified. Have you set GTHX_EMAIL_TO?")

        self.server = os.getenv("GTHX_EMAIL_SMTP_SERVER")
        if (self.server == None):
            raise ValueError("No SMTP server specified. Have you set GTHX_EMAIL_SMTP_SERVER?")

    def threadsend(self, subject, message):
        try:
            thread.start_new_thread(self.send, (subject, message))
        except Exception as e:
            print "Failed to start a thread email: %s", e
        
    def send(self, subject, message):
        if ((self.user != None) and (self.password != None) and (self.server != None)):
            print "Sending email notification..."

            # Create a text/plain message
            msg = "To: %s\n" % self.to_email
            msg += "From: %s\n" % self.from_email
            msg += "Subject: %s\n\n" % subject
            msg += message

            # Now send the message
            s = smtplib.SMTP(self.server)
            s.starttls()
            s.login(self.user, self.password)
            s.sendmail(self.from_email, [self.to_email], msg)
            s.quit()
            
            print "Done with email"

