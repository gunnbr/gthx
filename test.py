import unittest
import os

from DbAccess import DbAccess
from DbAccess import Seen
from DbAccess import Tell
from datetime import datetime

class DbAccessTest(unittest.TestCase):
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
        data = self.db.seen("somerandomuser")
        self.assertEqual(len(data), 0, "Returned data for a user that hasn't been seen")

    def test_valid_seen(self):
        user = "seenuser"
        channel = "#test_channel"
        message = "Running unit tests..."
        self.db.updateSeen(user, channel, message)

        data = self.db.seen(user)
        self.assertEqual(len(data), 1, "Returned incorrect data for a user that has been seen")

        self.assertEqual(row[Seen.name], user, "Wrong username returned for seen user")
        self.assertEqual(row[Seen.channel], channel, "Wrong channel returned for a seen user")
        #delta = 
        #self.assertEqual(row[Seen.timestamp], ???, "Wrong time returned for a seen user")
        self.assertEqual(row[Seen.message], message, "Wrong message returned for a seen user"))
        
        # TODO: Make way to remove a user from the seen table


if __name__ == '__main__':
    unittest.main()
    
