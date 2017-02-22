import unittest
import os
import time

from DbAccess import DbAccess
from DbAccess import Seen
from DbAccess import Tell
from datetime import datetime

class DbAccessTest(unittest.TestCase):
    missinguser = "somerandomuser"
    seenuser = "seenuser"
    seenuser2 = "seenuser2"
    
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
        data = self.db.seen(DbAccessTest.missinguser)
        self.assertEqual(len(data), 0, "Returned data for a user that hasn't been seen")

    def test_valid_seen(self):
        user = DbAccessTest.seenuser
        channel = "#test_channel"
        message = "Running unit tests..."
        self.db.updateSeen(user, channel, message)

        rows = self.db.seen(user)
        self.assertEqual(len(rows), 1, "Returned incorrect data for a user that has been seen")

        data=rows[0]
        
        self.assertEqual(data[Seen.name], user, "Wrong username returned for seen user")
        self.assertEqual(data[Seen.channel], channel, "Wrong channel returned for a seen user")

        delta = datetime.now() - data[Seen.timestamp]
        self.assertLess(delta.total_seconds(), 1, "Wrong time returned for a seen user")
        self.assertEqual(data[Seen.message], message, "Wrong message returned for a seen user")
        
        self.db.deleteSeen(user)

    def test_update_of_existing_seen(self):
        user = DbAccessTest.seenuser2
        channel = "#test_channel"
        message = "Running unit tests..."

        self.db.updateSeen(user, channel, message)

        # First test the normal case
        rows = self.db.seen(user)
        self.assertEqual(len(rows), 1, "Returned incorrect data for a user that has been seen")

        data=rows[0]
        
        delta = datetime.now() - data[Seen.timestamp]
        self.assertLess(delta.total_seconds(), 1, "Wrong time returned for a seen user")

        # Now wait a couple seconds and verify that the delta has changed
        time.sleep(2)

        rows = self.db.seen(user)
        self.assertEqual(len(rows), 1, "Returned incorrect data for a user that has been seen")

        data=rows[0]
        
        delta = datetime.now() - data[Seen.timestamp]
        self.assertGreater(delta.total_seconds(), 1, "Wrong time returned for a seen user")

        # Now update the same user again, then verify that the time has been updated.
        self.db.updateSeen(user, channel, message)

        rows = self.db.seen(user)
        self.assertEqual(len(rows), 1, "Returned incorrect data for a user that has been seen")

        data=rows[0]
        
        delta = datetime.now() - data[Seen.timestamp]
        self.assertLess(delta.total_seconds(), 1, "Wrong time returned for a seen user")
        
    def tearDown(self):
        self.db.deleteSeen(DbAccessTest.missinguser)
        self.db.deleteSeen(DbAccessTest.seenuser)
        self.db.deleteSeen(DbAccessTest.seenuser2)

if __name__ == '__main__':
    unittest.main()
    
