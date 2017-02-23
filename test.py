# -*- coding: utf-8 -*-
import unittest
import os
import time

from DbAccess import DbAccess
from DbAccess import Seen
from DbAccess import Tell
from datetime import datetime

class DbAccessSeenTest(unittest.TestCase):
    missinguser = "somerandomuser"
    seenuser = "seenuser"
    seenuser2 = "seenuser2"
    unicodeuser = "🐰Lover"
    
    def setUp(self):
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

    def test_missing_seen(self):
        data = self.db.seen(DbAccessSeenTest.missinguser)
        self.assertEqual(len(data), 0, "Returned data for a user that hasn't been seen")

    def test_valid_seen(self):
        user = DbAccessSeenTest.seenuser
        channel = "#test_channel"
        message = "Running unit tests..."
        self.db.updateSeen(user, channel, message)

        rows = self.db.seen(user)
        self.assertEqual(len(rows), 1, "Returned incorrect data for a user that has been seen")

        data=rows[0]
        
        self.assertEqual(data[Seen.name], user, "Wrong username returned for seen user")
        self.assertEqual(data[Seen.channel], channel, "Wrong channel returned for a seen user")

        delta = datetime.now() - data[Seen.timestamp]
        self.assertLess(delta.total_seconds(), 2, "Wrong time returned for a seen user: delta is %d" % delta.total_seconds())
        self.assertEqual(data[Seen.message], message, "Wrong message returned for a seen user")
        
        self.db.deleteSeen(user)

    def test_update_of_existing_seen(self):
        user = DbAccessSeenTest.seenuser2
        channel = "#test_channel"
        message = "Running unit tests..."

        self.db.updateSeen(user, channel, message)

        # First test the normal case
        rows = self.db.seen(user)
        self.assertEqual(len(rows), 1, "Returned incorrect data for a user that has been seen")

        data=rows[0]
        
        delta = datetime.now() - data[Seen.timestamp]
        self.assertLess(delta.total_seconds(), 2, 'Wrong time returned for a seen user: delta is %d' % (delta.total_seconds(), ))

        # Now wait a couple seconds and verify that the delta has changed
        time.sleep(2)

        rows = self.db.seen(user)
        self.assertEqual(len(rows), 1, "Returned incorrect data for a user that has been seen")

        data=rows[0]
        
        delta = datetime.now() - data[Seen.timestamp]
        self.assertGreater(delta.total_seconds(), 1, 'Wrong time returned for a seen user: delta is %d' % delta.total_seconds())

        # Now update the same user again, then verify that the time has been updated.
        self.db.updateSeen(user, channel, message)

        rows = self.db.seen(user)
        self.assertEqual(len(rows), 1, "Returned incorrect data for a user that has been seen")

        data=rows[0]
        
        delta = datetime.now() - data[Seen.timestamp]
        self.assertLess(delta.total_seconds(), 2, 'Wrong time returned for a seen user: delta is %d' % delta.total_seconds())

    # Test:
    # Add seen for user with unicode in the name
    # Add seen with message that has unicode in the name
    
    def tearDown(self):
        self.db.deleteSeen(DbAccessSeenTest.missinguser)
        self.db.deleteSeen(DbAccessSeenTest.seenuser)
        self.db.deleteSeen(DbAccessSeenTest.seenuser2)

class DbAccessFactoidTest(unittest.TestCase):

    missingFactoid = "missingfactoid"
    
    def setUp(self):
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

    # Test:
    # Fetch of factoid that doesn't exist
    # Add new factoid
    # Add and retrieve factoid with unicode factoid
    # Add and retrieve factoid with unicode definition
    # Replace existing factoid
    # Add to existing factoid
    # Replace existing factoid with multiple parts
    # Forget factoid
    # Forget factoid with multiple parts
    # Forget locked factoid
    # Factoid history for:
    #   Adding new
    #   Add additional
    #   Forget single factoid
    #   Forget multiple part factoid

    def test_get_missing_factoid(self):
        data = self.db.getFactoid(DbAccessFactoidTest.missingFactoid)
        self.assertFalse(data, "Got a valid return from a factoid that shouldn't exist")

#    def tearDown(self):
        # TODO: Clear all factoids
        # TODO: Clear factoid history


class DbAccessTellTest(unittest.TestCase):
    missinguser = "somerandomuser"
    
    def setUp(self):
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

    # Test:
    # Get tells for a user that doesn't have any waiting
    # Adding a tell
    # Get tells for a user that has some waiting
    # Get tells for the same user again to verify they're gone
    # Add tell to user with unicode in their name
    # Add tell with unicode in the message
    
    def test_get_with_no_tells(self):
        data = self.db.getTell(DbAccessTellTest.missinguser)
        self.assertFalse(data, "Got a valid return for a user with no tells waiting")
        
#    def tearDown(self):
        # TODO: Delete all tells
    
        
if __name__ == '__main__':
    unittest.main()
    
