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
    unicodemessage = "I love 🌮s"
    
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

    def test_update_of_seen_with_nick_including_backslashes(self):
        # These were found to cause problems in the real system
        user = "k\\o\\w"
        channel = "#test_channel"
        message = "Running unit tests..."

        self.db.updateSeen(user, channel, message)

        # First test the normal case
        rows = self.db.seen(user)
        self.assertEqual(len(rows), 1, "Returned incorrect data for a user that has been seen: %d" % len(rows))

        # Now update seen a few more times
        self.db.updateSeen(user, channel, message)
        self.db.updateSeen(user, channel, message)
        self.db.updateSeen(user, channel, message)
        self.db.updateSeen(user, channel, message)
        self.db.updateSeen(user, channel, message)
        
        rows = self.db.seen(user)
        self.assertEqual(len(rows), 1, "Returned incorrect data for a user that has been seen")


    def test_sql_injection_through_seen(self):
        # SELECT * FROM seen WHERE name LIKE
        # blah; DROP TABLE SEEN; SELECT * FROM SEEN WHERE name LIKE blah
        # ORDER BY timestamp DESC LIMIT 3
        # These were found to cause problems in the real system
        #user = "blah; DROP TABLE SEEN; SELECT * FROM SEEN WHERE name LIKE blah"
        user = "blah; DROP TABLE SEEN;"
        channel = "#test_channel"
        message = "Running unit tests..."

        self.db.updateSeen(user, channel, message)

        # First test the normal case
        rows = self.db.seen(user)
        self.assertEqual(len(rows), 1, "Returned incorrect data for a user that has been seen: %d" % len(rows))
        
    def test_unicode_seen(self):
        user = DbAccessSeenTest.unicodeuser
        channel = "#test_channel"
        message = DbAccessSeenTest.unicodemessage

        self.db.updateSeen(user, channel, message)

        rows = self.db.seen(user)
        self.assertEqual(len(rows), 1, "Returned incorrect data for a unicode user that has been seen")

        data=rows[0]
        
        self.assertEqual(data[Seen.name], user, "Wrong username returned for a unicode seen user")
        self.assertEqual(data[Seen.channel], channel, "Wrong channel returned for a unicode seen user")

        delta = datetime.now() - data[Seen.timestamp]
        self.assertLess(delta.total_seconds(), 2, "Wrong time returned for a unicode seen user: delta is %d" % delta.total_seconds())
        self.assertEqual(data[Seen.message], message, "Wrong message returned for a unicode seen message")
        
        self.db.deleteSeen(user)
    
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

    def test_get_missing_factoid(self):
        data = self.db.getFactoid(DbAccessFactoidTest.missingFactoid)
        self.assertFalse(data, "Got a valid return from a factoid that shouldn't exist")

    def test_add_factoid(self):
        user="someuser"
        item="somefactoid"
        isAre=False
        definition="a good thing to talk about"
        overwrite=False
        
        success = self.db.addFactoid(user, item, isAre, definition, overwrite)

        self.assertTrue(success, "Failed to add a new factoid")
        
        data = self.db.getFactoid(item)
        self.assertEqual(len(data), 1, "Returned wrong number of results for a factoid: %d" % (len(data),) )

        factoid=data[0]
        
        # TODO: I really need to make this data access more intuitive to use
        self.assertEquals(factoid[1], item, "Factoid failed to retrieve the item field correctly")
        self.assertEquals(factoid[2], isAre, "Factoid failed to retrieve the is/are field correctly")
        self.assertEquals(factoid[3], definition, "Factoid failed to retrieve the defintion correctly")
        self.assertEquals(factoid[4], user, "Factoid failed to retrieve the user correctly")

        delta = datetime.now() - factoid[5]
        self.assertLess(delta.total_seconds(), 2, "Wrong time returned for a factoid date set: delta is %d" % delta.total_seconds())

        self.assertFalse(factoid[6], "Factoid failed to retrieve the locked flag correctly")

    def test_add_unicode_factoid(self):
        user="some😀user"
        item="some🐶factoid"
        isAre=False
        definition="a good thing to eat 🍕🌮🍜🎂🍧"
        overwrite=False
        
        success = self.db.addFactoid(user, item, isAre, definition, overwrite)

        self.assertTrue(success, "Failed to add a new factoid")
        
        data = self.db.getFactoid(item)
        self.assertEqual(len(data), 1, "Returned wrong number of results for a factoid: %d" % (len(data),) )

        factoid=data[0]
        
        self.assertEquals(factoid[1], item, "Factoid failed to retrieve the item field correctly")
        self.assertEquals(factoid[2], isAre, "Factoid failed to retrieve the is/are field correctly")
        self.assertEquals(factoid[3], definition, "Factoid failed to retrieve the defintion correctly")
        self.assertEquals(factoid[4], user, "Factoid failed to retrieve the user correctly")

        delta = datetime.now() - factoid[5]
        self.assertLess(delta.total_seconds(), 2, "Wrong time returned for a factoid date set: delta is %d" % delta.total_seconds())

        self.assertFalse(factoid[6], "Factoid failed to retrieve the locked flag correctly")

    def test_add_to_factoid_then_replace(self):
        user="someuser"
        user2="someotheruser"
        user3="someguy"
        item="somefactoid"
        isAre=True
        definition="a good thing to talk about"
        definition2="something people write"
        replacement="stupid facts"
        
        success = self.db.addFactoid(user, item, isAre, definition, False)
        self.assertTrue(success, "Failed to add a new factoid")

        success = self.db.addFactoid(user2, item, isAre, definition2, False)
        self.assertTrue(success, "Failed to add a new factoid")
        
        data = self.db.getFactoid(item)
        self.assertEqual(len(data), 2, "Returned wrong number of results for a multi-factoid: %d" % (len(data),) )

        factoid=data[0]
        
        self.assertEquals(factoid[1], item, "Factoid failed to retrieve the item field correctly")
        self.assertEquals(factoid[2], isAre, "Factoid failed to retrieve the is/are field correctly")
        self.assertEquals(factoid[3], definition, "Factoid failed to retrieve the defintion correctly")
        self.assertEquals(factoid[4], user, "Factoid failed to retrieve the user correctly")

        delta = datetime.now() - factoid[5]
        self.assertLess(delta.total_seconds(), 2, "Wrong time returned for a factoid date set: delta is %d" % delta.total_seconds())

        self.assertFalse(factoid[6], "Factoid failed to retrieve the locked flag correctly")

        factoid=data[1]
        
        self.assertEquals(factoid[1], item, "Factoid failed to retrieve the item field correctly")
        self.assertEquals(factoid[2], isAre, "Factoid failed to retrieve the is/are field correctly")
        self.assertEquals(factoid[3], definition2, "Factoid failed to retrieve the defintion correctly")
        self.assertEquals(factoid[4], user2, "Factoid failed to retrieve the user correctly")

        delta = datetime.now() - factoid[5]
        self.assertLess(delta.total_seconds(), 2, "Wrong time returned for a factoid date set: delta is %d" % delta.total_seconds())

        self.assertFalse(factoid[6], "Factoid failed to retrieve the locked flag correctly")

        # Now overwrite these definitions with a totally new one
        success = self.db.addFactoid(user3, item, isAre, replacement, True)
        self.assertTrue(success, "Failed to replace a new factoid")
        
        data = self.db.getFactoid(item)
        self.assertEqual(len(data), 1, "Returned wrong number of results for a replacedfactoid: %d" % (len(data),) )

        factoid=data[0]
        
        self.assertEquals(factoid[1], item, "Factoid failed to retrieve the item field correctly")
        self.assertEquals(factoid[2], isAre, "Factoid failed to retrieve the is/are field correctly")
        self.assertEquals(factoid[3], replacement, "Factoid failed to retrieve the defintion correctly")
        self.assertEquals(factoid[4], user3, "Factoid failed to retrieve the user correctly")

        delta = datetime.now() - factoid[5]
        self.assertLess(delta.total_seconds(), 2, "Wrong time returned for a factoid date set: delta is %d" % delta.total_seconds())

        self.assertFalse(factoid[6], "Factoid failed to retrieve the locked flag correctly")
        
    def test_forget_factoid(self):
        user="someuser"
        user2="someotheruser"
        user3="someguy"
        item="somefactoid"
        isAre=True
        definition="a good thing to talk about"
        definition2="something people write"
        
        success = self.db.addFactoid(user, item, isAre, definition, False)
        self.assertTrue(success, "Failed to add a new factoid")

        success = self.db.addFactoid(user2, item, isAre, definition2, False)
        self.assertTrue(success, "Failed to add a new factoid")

        wasDeleted = self.db.forgetFactoid(item, user3)
        self.assertTrue(wasDeleted, "Incorect return value from forgetFactoid")

        data = self.db.getFactoid(item)
        self.assertEqual(len(data), 0, "Returned wrong number of results for a forgotten factoid: %d" % (len(data),) )

    def test_forget_factoid_that_doesnt_exist(self):
        user="someuser"
        item="somefactoid"
        
        wasDeleted = self.db.forgetFactoid(item, user)
        self.assertFalse(wasDeleted, "Incorrect return value from forgetFactoid")


    def test_lock_and_replace_or_forget_factoid(self):
        user="someuser"
        item="lockedfactoid"
        isAre=True
        definition="a good thing to talk about"
        overwrite=False
        
        success = self.db.addFactoid(user, item, isAre, definition, False)
        self.assertTrue(success, "Failed to add a new factoid")

        self.db.lockFactoid(item)
        
        data = self.db.getFactoid(item)
        self.assertEqual(len(data), 1, "Returned wrong number of results for a factoid: %d" % (len(data),) )

        factoid=data[0]
        
        self.assertTrue(factoid[6], "Factoid does not appear to be locked when it should be")

        wasDeleted = self.db.forgetFactoid(item, user)
        self.assertFalse(wasDeleted, "Was incorrrectly able to delete a locked factoid")
        
        success = self.db.addFactoid(user, item, isAre, definition, True)
        self.assertFalse(success, "Was incorrectly able to replace a locked factoid")
        
    # Test:
    # Factoid history for:
    #   Adding new
    #   Add additional
    #   Forget single factoid
    #   Forget multiple part factoid

    def tearDown(self):
        # Clear all factoids and history
        self.db.deleteAllFactoids()
        #print "Skipping factoid teardown"


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

    def test_user_with_no_tells(self):
        user="someuser"

        data = self.db.getTell(user)
        self.assertEquals(len(data), 0, "Wrong number of tells returned for a user who doesn't have any waiting")
        
    def test_get_with_no_tells(self):
        data = self.db.getTell(DbAccessTellTest.missinguser)
        self.assertFalse(data, "Got a valid return for a user with no tells waiting")
        
    def test_add_and_get_and_verify_tell(self):
        teller = "talker"
        receiver = "randomuser"
        message = "Ping me when you can"
        kthxKnows = False
        
        success = self.db.addTell(teller, receiver, message, kthxKnows)
        self.assertTrue(success, "Failed to add a tell to a user");
        
        data = self.db.getTell(receiver)
        self.assertTrue(data, "Got no tells for a user with tells waiting")
        self.assertEquals(len(data), 1, "Got wrong number of tells for a user")
        
        tell = data[0]
        self.assertEquals(tell[1], teller, "Got wrong author for a tell")
        self.assertEquals(tell[2], receiver, "Got wrong recipient for a tell")
        self.assertEquals(tell[4], message, "Got wrong message for a tell")
        self.assertEquals(tell[5], kthxKnows, "Got wrong inTracked for a tell")

        delta = datetime.now() - tell[3]
        self.assertLess(delta.total_seconds(), 2, "Wrong time returned for a tell date set: delta is %d" % delta.total_seconds())

        # Now get again for the same user to make sure they've been cleared
        data = self.db.getTell(receiver)
        self.assertFalse(data, "Got tells for a user with none waiting")
        
    def test_add_and_get_and_verify_unicode_tell(self):
        teller = "😇talker"
        receiver = "random🚕user"
        message = "☎️ me when you can"
        kthxKnows = True
        
        success = self.db.addTell(teller, receiver, message, kthxKnows)
        self.assertTrue(success, "Failed to add a tell to a user");
        
        data = self.db.getTell(receiver)
        self.assertTrue(data, "Got no tells for a user with tells waiting")
        self.assertEquals(len(data), 1, "Got wrong number of tells for a user")
        
        tell = data[0]
        self.assertEquals(tell[1], teller, "Got wrong author for a tell")
        self.assertEquals(tell[2], receiver, "Got wrong recipient for a tell")
        self.assertEquals(tell[4], message, "Got wrong message for a tell")
        self.assertEquals(tell[5], kthxKnows, "Got wrong inTracked for a tell")

        delta = datetime.now() - tell[3]
        self.assertLess(delta.total_seconds(), 2, "Wrong time returned for a tell date set: delta is %d" % delta.total_seconds())

        # Now get again for the same user to make sure they've been cleared
        data = self.db.getTell(receiver)
        self.assertFalse(data, "Got tells for a user with none waiting")
        
    def test_multiple_tells(self):
        teller = "talker"
        teller2 = "another_talker"
        teller3 = "schminkebob"
        receiver = "randomuser"
        message = "Ping me when you can"
        message2 = "Can you give me a ring please?"
        message3 = "WAKE UP!!"
        kthxKnows = False
        kthxKnows2 = True
        kthxKnows3 = False
        
        success = self.db.addTell(teller, receiver, message, kthxKnows)
        self.assertTrue(success, "Failed to add a tell to a user");
        success = self.db.addTell(teller2, receiver, message2, kthxKnows2)
        self.assertTrue(success, "Failed to add a second tell to a user");
        success = self.db.addTell(teller3, receiver, message3, kthxKnows3)
        self.assertTrue(success, "Failed to add a third tell to a user");
        
        data = self.db.getTell(receiver)
        self.assertTrue(data, "Got no tells for a user with tells waiting")
        self.assertEquals(len(data), 3, "Got wrong number of tells for a user")
        
        tell = data[0]
        self.assertEquals(tell[1], teller, "Got wrong author for a tell")
        self.assertEquals(tell[2], receiver, "Got wrong recipient for a tell")
        self.assertEquals(tell[4], message, "Got wrong message for a tell")
        self.assertEquals(tell[5], kthxKnows, "Got wrong inTracked for a tell")

        delta = datetime.now() - tell[3]
        self.assertLess(delta.total_seconds(), 2, "Wrong time returned for a tell date set: delta is %d" % delta.total_seconds())

        tell = data[1]
        self.assertEquals(tell[1], teller2, "Got wrong author for a tell")
        self.assertEquals(tell[2], receiver, "Got wrong recipient for a tell")
        self.assertEquals(tell[4], message2, "Got wrong message for a tell")
        self.assertEquals(tell[5], kthxKnows2, "Got wrong inTracked for a tell")

        delta = datetime.now() - tell[3]
        self.assertLess(delta.total_seconds(), 2, "Wrong time returned for a tell date set: delta is %d" % delta.total_seconds())

        tell = data[2]
        self.assertEquals(tell[1], teller3, "Got wrong author for a tell")
        self.assertEquals(tell[2], receiver, "Got wrong recipient for a tell")
        self.assertEquals(tell[4], message3, "Got wrong message for a tell")
        self.assertEquals(tell[5], kthxKnows3, "Got wrong inTracked for a tell")

        delta = datetime.now() - tell[3]
        self.assertLess(delta.total_seconds(), 2, "Wrong time returned for a tell date set: delta is %d" % delta.total_seconds())

        # Now get again for the same user to make sure they've been cleared
        data = self.db.getTell(receiver)
        self.assertFalse(data, "Got tells for a user with none waiting")
    
    def tearDown(self):
        self.db.deleteAllTells()
    
        
if __name__ == '__main__':
    unittest.main()
    
