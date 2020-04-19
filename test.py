# -*- coding: utf-8 -*-
import unittest
import os
import time
import configparser

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
        config = configparser.ConfigParser()
        results = config.read('gthx.config.local')
        if not results:
            raise SystemExit("Failed to read config file 'gthx.config.local'")
        dbHost = config.get('MYSQL','GTHX_MYSQL_HOST')
        dbUser = config.get('MYSQL','GTHX_MYSQL_USER')
        dbPassword = config.get('MYSQL','GTHX_MYSQL_PASSWORD')
        dbName = config.get('MYSQL','GTHX_MYSQL_DATABASE')

        self.db = DbAccess(dbHost, dbUser, dbPassword, dbName)

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
    def setUp(self):
        config = configparser.ConfigParser()
        results = config.read('gthx.config.local')
        if not results:
            raise SystemExit("Failed to read config file 'gthx.config.local'")
        dbHost = config.get('MYSQL','GTHX_MYSQL_HOST')
        dbUser = config.get('MYSQL','GTHX_MYSQL_USER')
        dbPassword = config.get('MYSQL','GTHX_MYSQL_PASSWORD')
        dbName = config.get('MYSQL','GTHX_MYSQL_DATABASE')

        self.db = DbAccess(dbHost, dbUser, dbPassword, dbName)

    def test_get_missing_factoid(self):
        missingFactoid = "missingfactoid"
        data = self.db.getFactoid(missingFactoid)
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
        self.assertEqual(factoid[1], item, "Factoid failed to retrieve the item field correctly")
        self.assertEqual(factoid[2], isAre, "Factoid failed to retrieve the is/are field correctly")
        self.assertEqual(factoid[3], definition, "Factoid failed to retrieve the defintion correctly")
        self.assertEqual(factoid[4], user, "Factoid failed to retrieve the user correctly")

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
        
        self.assertEqual(factoid[1], item, "Factoid failed to retrieve the item field correctly")
        self.assertEqual(factoid[2], isAre, "Factoid failed to retrieve the is/are field correctly")
        self.assertEqual(factoid[3], definition, "Factoid failed to retrieve the defintion correctly")
        self.assertEqual(factoid[4], user, "Factoid failed to retrieve the user correctly")

        delta = datetime.now() - factoid[5]
        self.assertLess(delta.total_seconds(), 2, "Wrong time returned for a factoid date set: delta is %d" % delta.total_seconds())

        self.assertFalse(factoid[6], "Factoid failed to retrieve the locked flag correctly")

    def test_add_to_factoid_then_replace(self):
        user="someuser"
        user2="someotheruser"
        user3="someguy"
        item="somefactoidToReplace"
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
        
        self.assertEqual(factoid[1], item, "Factoid failed to retrieve the item field correctly")
        self.assertEqual(factoid[2], isAre, "Factoid failed to retrieve the is/are field correctly")
        self.assertEqual(factoid[3], definition, "Factoid failed to retrieve the defintion correctly")
        self.assertEqual(factoid[4], user, "Factoid failed to retrieve the user correctly")

        delta = datetime.now() - factoid[5]
        self.assertLess(delta.total_seconds(), 2, "Wrong time returned for a factoid date set: delta is %d" % delta.total_seconds())

        self.assertFalse(factoid[6], "Factoid failed to retrieve the locked flag correctly")

        factoid=data[1]
        
        self.assertEqual(factoid[1], item, "Factoid failed to retrieve the item field correctly")
        self.assertEqual(factoid[2], isAre, "Factoid failed to retrieve the is/are field correctly")
        self.assertEqual(factoid[3], definition2, "Factoid failed to retrieve the defintion correctly")
        self.assertEqual(factoid[4], user2, "Factoid failed to retrieve the user correctly")

        delta = datetime.now() - factoid[5]
        self.assertLess(delta.total_seconds(), 2, "Wrong time returned for a factoid date set: delta is %d" % delta.total_seconds())

        self.assertFalse(factoid[6], "Factoid failed to retrieve the locked flag correctly")

        # Now overwrite these definitions with a totally new one
        success = self.db.addFactoid(user3, item, isAre, replacement, True)
        self.assertTrue(success, "Failed to replace a new factoid")
        
        data = self.db.getFactoid(item)
        self.assertEqual(len(data), 1, "Returned wrong number of results for a replacedfactoid: %d" % (len(data),) )

        factoid=data[0]
        
        self.assertEqual(factoid[1], item, "Factoid failed to retrieve the item field correctly")
        self.assertEqual(factoid[2], isAre, "Factoid failed to retrieve the is/are field correctly")
        self.assertEqual(factoid[3], replacement, "Factoid failed to retrieve the defintion correctly")
        self.assertEqual(factoid[4], user3, "Factoid failed to retrieve the user correctly")

        delta = datetime.now() - factoid[5]
        self.assertLess(delta.total_seconds(), 2, "Wrong time returned for a factoid date set: delta is %d" % delta.total_seconds())

        self.assertFalse(factoid[6], "Factoid failed to retrieve the locked flag correctly")
        
    def test_forget_factoid(self):
        user="someuser"
        user2="someotheruser"
        user3="someguy"
        item="somefactoidToForget"
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
        item="somefactoidThatIsntHere"
        
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
        
    def test_factoid_info(self):
        user="someguy"
        counteditem="countedfactoid"
        isAre=False
        definition="something to test"
        overwrite=False

        # Verify that this factoid has no history to start
        info = self.db.infoFactoid(counteditem)
        self.assertFalse(info, "Factoid has info when it shouldn't.")

        # Add the factoid
        success = self.db.addFactoid(user, counteditem, isAre, definition, overwrite)
        self.assertTrue(success, "Failed to add a new factoid")

        # Verify that it now has some history
        info = self.db.infoFactoid(counteditem)
        self.assertTrue(info, "Factoid has no info when it should.")

        # Verify that there's just one of info
        self.assertEqual(len(info), 1, "Factoid doesn't have the correct amount of info")

        # And verify that the info is correct
        history = info[0]
        self.assertEqual(history[1], counteditem, "Factoid history has the wrong item name")
        self.assertEqual(history[2], definition, "Factoid history has the wrong definition")
        self.assertEqual(history[3], user, "Factoid history has the wrong username")
        delta = datetime.now() - history[4]
        self.assertLess(delta.total_seconds(), 2, "Factoid history has the wrong time. delta is %d" % delta.total_seconds())
        self.assertIsNone(history[5], "Factoid history has the wrong item name the second place: %s" % history[5])
        self.assertIsNone(history[6], "Factoid history has the wrong count: %s" % history[6])
        self.assertIsNone(history[7], "Factoid history has the wrong last referenced time: %s" % history[7])
                        
        # Now do a reference...
        data = self.db.getFactoid(counteditem)

        # ...and verify that the info gets updated
        info = self.db.infoFactoid(counteditem)
        self.assertTrue(info, "Factoid has no info when it should.")

        # Verify that there's still just one of info
        self.assertEqual(len(info), 1, "Factoid doesn't have the correct amount of info")

        # And verify that the info is correct
        history = info[0]
        self.assertEqual(history[1], counteditem, "Factoid history has the wrong item name")
        self.assertEqual(history[2], definition, "Factoid history has the wrong definition")
        self.assertEqual(history[3], user, "Factoid history has the wrong username")
        delta = datetime.now() - history[4]
        self.assertLess(delta.total_seconds(), 2, "Factoid history has the wrong time. delta is %d" % delta.total_seconds())
        self.assertEqual(history[5], counteditem, "Factoid history has the wrong item name the second place: %s" % history[5])
        self.assertEqual(history[6], 1, "Factoid history has the wrong count: %s" % history[6])
        delta = datetime.now() - history[7]
        self.assertLess(delta.total_seconds(), 2, "Factoid history has the wrong time. delta is %d" % delta.total_seconds())
        
        # Finally do a few more references
        data = self.db.getFactoid(counteditem)
        data = self.db.getFactoid(counteditem)
        data = self.db.getFactoid(counteditem)
        data = self.db.getFactoid(counteditem)

        # ...and verify that the info gets updated
        info = self.db.infoFactoid(counteditem)
        self.assertTrue(info, "Factoid has no info when it should.")

        # Verify that there's still just one of info
        self.assertEqual(len(info), 1, "Factoid doesn't have the correct amount of info")

        # And verify that the info is correct
        history = info[0]
        self.assertEqual(history[1], counteditem, "Factoid history has the wrong item name")
        self.assertEqual(history[2], definition, "Factoid history has the wrong definition")
        self.assertEqual(history[3], user, "Factoid history has the wrong username")
        delta = datetime.now() - history[4]
        self.assertLess(delta.total_seconds(), 2, "Factoid history has the wrong time. delta is %d" % delta.total_seconds())
        self.assertEqual(history[5], counteditem, "Factoid history has the wrong item name the second place: %s" % history[5])
        self.assertEqual(history[6], 5, "Factoid history has the wrong count: %s" % history[6])
        delta = datetime.now() - history[7]
        self.assertLess(delta.total_seconds(), 2, "Factoid history has the wrong time. delta is %d" % delta.total_seconds())
        
    def test_get_factoid_doesnt_set_refs(self):
        user="someguy"
        nonexistantitem="not_a_factoid"

        # Verify that this factoid has no history to start
        info = self.db.infoFactoid(nonexistantitem)
        self.assertFalse(info, "Factoid has info when it shouldn't.")

        # Now do a reference...
        data = self.db.getFactoid(nonexistantitem)
        self.assertFalse(data, "Factoid exists when it shouldn't.")

        # Verify that this factoid still has no history
        info = self.db.infoFactoid(nonexistantitem)
        self.assertFalse(info, "Factoid has info when it shouldn't.")

    def test_info_for_forget_factoid(self):
        user="someguy"
        userWhoDeletes="killer"
        item="forgottenfactoid"
        isAre=False
        definition="something to test"

        # Add the factoid
        success = self.db.addFactoid(user, item, isAre, definition, False)
        self.assertTrue(success, "Failed to add a new factoid")

        # Verify that it now has some history
        info = self.db.infoFactoid(item)
        self.assertTrue(info, "Factoid has no info when it should.")

        # Verify that there's just one of info
        self.assertEqual(len(info), 1, "Factoid doesn't have the correct amount of info")

        # Now forget it..
        status = self.db.forgetFactoid(item,userWhoDeletes)

        # ...and verify that the info gets updated
        info = self.db.infoFactoid(item)
        self.assertTrue(info, "Factoid has no info when it should.")

        # Verify that there are 2 entries now
        self.assertEqual(len(info), 2, "Factoid doesn't have the correct amount of info")

        # Verify that the first entry correctly specifies the add
        history = info[0]
        self.assertEqual(history[1], item, "Factoid history has the wrong item name")
        self.assertEqual(history[2], definition, "Factoid history has the wrong definition: '%s'" % history[2])
        self.assertEqual(history[3], user, "Factoid history has the wrong username")
        delta = datetime.now() - history[4]
        self.assertLess(delta.total_seconds(), 2, "Factoid history has the wrong time. delta is %d" % delta.total_seconds())
        self.assertIsNone(history[5], "Factoid history ref count has an item name when it shouldn't.")
        self.assertIsNone(history[6], "Factoid history has a count when it shouldn't")
        self.assertIsNone(history[7], "Factoid history has a last referenced time when it shouldn't.")
        
        # Verify that the second entry correctly specifies the forget
        history = info[1]
        self.assertEqual(history[1], item, "Factoid history has the wrong item name")
        self.assertIsNone(history[2], "Factoid history for forgotten entry has a definition when it shouldn't")
        self.assertEqual(history[3], userWhoDeletes, "Factoid history for forgotten entry has the wrong username")
        delta = datetime.now() - history[4]
        self.assertLess(delta.total_seconds(), 2, "Factoid history has the wrong time. delta is %d" % delta.total_seconds())
        self.assertIsNone(history[5], "Factoid history ref count has an item name when it shouldn't.")
        self.assertIsNone(history[6], "Factoid history has a count when it shouldn't")
        self.assertIsNone(history[7], "Factoid history has a last referenced time when it shouldn't.")

        # Now reference this factoid and see if it gets added to the ref count
        data = self.db.getFactoid(item)
        
        info = self.db.infoFactoid(item)
        self.assertTrue(info, "Factoid has no info when it should.")
        self.assertEqual(len(info), 2, "Factoid doesn't have the correct amount of info")

        # Verify that there is still no ref count
        history = info[0]
        self.assertIsNone(history[5], "Factoid history ref does not contain the correct item.")
        self.assertIsNone(history[6], "Factoid history has a ref count when it shouldn't: %s" % history[6])
        self.assertIsNone(history[7], "Factoid history has a reference time when it shouldn't")
        
    def test_ref_count_for_forget_factoid(self):
        user="someguy"
        userWhoDeletes="killer"
        item="hereGoneBackAgain"
        isAre=False
        definition="a factoid that keeps disappearing"

        # Add the factoid
        success = self.db.addFactoid(user, item, isAre, definition, False)
        self.assertTrue(success, "Failed to add a new factoid")

        # Verify that it now has some history
        info = self.db.infoFactoid(item)
        self.assertTrue(info, "Factoid has no info when it should.")
        self.assertEqual(len(info), 1, "Factoid doesn't have the correct amount of info")

        # Reference it
        data = self.db.getFactoid(item)
        
        # Now forget it..
        status = self.db.forgetFactoid(item,userWhoDeletes)

        # ...and verify that the ref count still exists
        info = self.db.infoFactoid(item)
        self.assertTrue(info, "Factoid has no info when it should.")
        self.assertEqual(len(info), 2, "Factoid doesn't have the correct amount of info")

        # Verify that the ref count still exists
        history = info[0]
        self.assertEqual(history[6], 1, "Factoid history ref count is incorrect: %s" % history[6])
        history = info[1]
        self.assertEqual(history[6], 1, "Factoid history ref count is incorrect: %s" % history[6])

        # Now reference again now that it's deleted...
        data = self.db.getFactoid(item)
        
        info = self.db.infoFactoid(item)
        self.assertTrue(info, "Factoid has no info when it should.")
        self.assertEqual(len(info), 2, "Factoid doesn't have the correct amount of info")

        # Verify that the ref count hasn't changed
        history = info[0]
        self.assertEqual(history[6], 1, "Factoid history ref count is incorrect: %s" % history[6])
        history = info[1]
        self.assertEqual(history[6], 1, "Factoid history ref count is incorrect: %s" % history[6])

    def test_info_for_forget_factoid(self):
        user="someguy"
        user2="otherguy"
        userWhoDeletes="killer"
        item="multifactoid"
        isAre=False
        definition="something to test"
        definition2="something to forget"

        # Add the factoid
        success = self.db.addFactoid(user, item, isAre, definition, False)
        self.assertTrue(success, "Failed to add a new factoid")

        # Add a second entry
        success = self.db.addFactoid(user2, item, isAre, definition2, False)
        self.assertTrue(success, "Failed to add a second entry to a factoid")
        
        # Now forget it..
        status = self.db.forgetFactoid(item,userWhoDeletes)

        # Verify that it now has some history
        info = self.db.infoFactoid(item)
        self.assertTrue(info, "Factoid has no info when it should.")

        # Verify that there are 3 info entries
        self.assertEqual(len(info), 3, "Factoid doesn't have the correct amount of info")

        # Verify that the first entry correctly specifies the forget
        history = info[0]
        self.assertEqual(history[1], item, "Factoid history has the wrong item name")
        self.assertIsNone(history[2], "Factoid history has the wrong definition: '%s'" % history[2])
        self.assertEqual(history[3], userWhoDeletes, "Factoid history has the wrong username")
        delta = datetime.now() - history[4]
        self.assertLess(delta.total_seconds(), 2, "Factoid history has the wrong time. delta is %d" % delta.total_seconds())
        self.assertIsNone(history[5], "Factoid history ref count has an item name when it shouldn't.")
        self.assertIsNone(history[6], "Factoid history has a count when it shouldn't")
        self.assertIsNone(history[7], "Factoid history has a last referenced time when it shouldn't.")
        
        # Verify that the second entry correctly specifies the second add
        history = info[1]
        self.assertEqual(history[1], item, "Factoid history has the wrong item name")
        self.assertEqual(history[2], definition2, "Factoid history has the wrong definition: '%s'" % history[2])
        self.assertEqual(history[3], user2, "Factoid history has the wrong username")
        delta = datetime.now() - history[4]
        self.assertLess(delta.total_seconds(), 2, "Factoid history has the wrong time. delta is %d" % delta.total_seconds())
        self.assertIsNone(history[5], "Factoid history ref count has an item name when it shouldn't.")
        self.assertIsNone(history[6], "Factoid history has a count when it shouldn't")
        self.assertIsNone(history[7], "Factoid history has a last referenced time when it shouldn't.")

        # Verify that the third entry correctly specifies the first add
        history = info[2]
        self.assertEqual(history[1], item, "Factoid history has the wrong item name")
        self.assertEqual(history[2], definition, "Factoid history for forgotten entry has a definition when it shouldn't")
        self.assertEqual(history[3], user, "Factoid history for forgotten entry has the wrong username")
        delta = datetime.now() - history[4]
        self.assertLess(delta.total_seconds(), 2, "Factoid history has the wrong time. delta is %d" % delta.total_seconds())
        self.assertIsNone(history[5], "Factoid history ref count has an item name when it shouldn't.")
        self.assertIsNone(history[6], "Factoid history has a count when it shouldn't")
        self.assertIsNone(history[7], "Factoid history has a last referenced time when it shouldn't.")

    def test_overwrite_multipart_factoid(self):
        user="someguy"
        user2="otherguy"
        user3="overwriter"
        item="multiforgottenfactoid"
        isAre=True
        definition="something to test"
        definition2="something to forget"
        definition3="the REAL definition"

        # Add the factoid
        success = self.db.addFactoid(user, item, isAre, definition, False)
        self.assertTrue(success, "Failed to add a new factoid")

        # Add a second entry
        success = self.db.addFactoid(user2, item, isAre, definition2, False)
        self.assertTrue(success, "Failed to add a second entry to a factoid")
        
        # Overwrite them with a new one
        success = self.db.addFactoid(user3, item, isAre, definition3, True)
        self.assertTrue(success, "Failed to overwrite a multi-part factoid")

        # Verify that it now has some history
        info = self.db.infoFactoid(item)
        self.assertTrue(info, "Factoid has no info when it should.")
        self.assertEqual(len(info), 4, "Factoid doesn't have the correct amount of info")

        # Verify that the first entry correctly specifies the overwrite
        history = info[0]
        self.assertEqual(history[1], item, "Factoid history has the wrong item name")
        self.assertEqual(history[2], definition3, "Factoid history has wrong definition: '%s'" % history[2])
        self.assertEqual(history[3], user3, "Factoid history has the wrong username")
        delta = datetime.now() - history[4]
        self.assertLess(delta.total_seconds(), 2, "Factoid history has the wrong time. delta is %d" % delta.total_seconds())
        self.assertIsNone(history[5], "Factoid history ref count has an item name when it shouldn't.")
        self.assertIsNone(history[6], "Factoid history has a count when it shouldn't")
        self.assertIsNone(history[7], "Factoid history has a last referenced time when it shouldn't.")
        
        # Verify that the second entry correctly specifies a forget (trigger by the overwrite)
        history = info[1]
        self.assertEqual(history[1], item, "Factoid history has the wrong item name")
        self.assertIsNone(history[2], "Factoid history has the definition when it shouldn't: '%s'" % history[2])
        self.assertEqual(history[3], user3, "Factoid history has the wrong username")
        delta = datetime.now() - history[4]
        self.assertLess(delta.total_seconds(), 2, "Factoid history has the wrong time. delta is %d" % delta.total_seconds())
        self.assertIsNone(history[5], "Factoid history ref count has an item name when it shouldn't.")
        self.assertIsNone(history[6], "Factoid history has a count when it shouldn't")
        self.assertIsNone(history[7], "Factoid history has a last referenced time when it shouldn't.")

        # Verify that the third entry correctly specifies the second add
        history = info[2]
        self.assertEqual(history[1], item, "Factoid history has the wrong item name")
        self.assertEqual(history[2], definition2, "Factoid history has a definition: %s" % history[2])
        self.assertEqual(history[3], user2, "Factoid history for forgotten entry has the wrong username")
        delta = datetime.now() - history[4]
        self.assertLess(delta.total_seconds(), 2, "Factoid history has the wrong time. delta is %d" % delta.total_seconds())
        self.assertIsNone(history[5], "Factoid history ref count has an item name when it shouldn't.")
        self.assertIsNone(history[6], "Factoid history has a count when it shouldn't")
        self.assertIsNone(history[7], "Factoid history has a last referenced time when it shouldn't.")

        # Verify that the fourth entry correctly specifies the first add
        history = info[3]
        self.assertEqual(history[1], item, "Factoid history has the wrong item name")
        self.assertEqual(history[2], definition, "Factoid history has the wrong definition: '%s'" % history[2])
        self.assertEqual(history[3], user, "Factoid history has the wrong username")
        delta = datetime.now() - history[4]
        self.assertLess(delta.total_seconds(), 2, "Factoid history has the wrong time. delta is %d" % delta.total_seconds())
        self.assertIsNone(history[5], "Factoid history ref count has an item name when it shouldn't.")
        self.assertIsNone(history[6], "Factoid history has a count when it shouldn't")
        self.assertIsNone(history[7], "Factoid history has a last referenced time when it shouldn't.")

    def test_mood(self):
        # Testing mood here because it relies on factoids

        # Test that mood is initially 0 even with botsnack and botsmack
        # not in the DB
        mood = self.db.mood()
        self.assertEqual(mood, 0, "Empty DB returned wrong mood")

        # Add the factoids
        success = self.db.addFactoid("testuser", "botsnack", 0, "<reply>Thank you!", False)
        success = self.db.addFactoid("testuser", "botsmack", 0, "<reply>OUCH!", False)

        # Give the bot 1 snack...
        self.db.getFactoid("botsnack")
        
        # ...and make sure the mood is 1
        mood = self.db.mood()
        self.assertEqual(mood, 1, "After botsnack returned the wrong mood")

        # Smack it down...
        self.db.getFactoid("botsmack")

        # ...and verify we're back at 0
        mood = self.db.mood()
        self.assertEqual(mood, 0, "After equal snacks and smacks, mood is not 0")

        # A couple more snacks...        
        self.db.getFactoid("botsnack")
        self.db.getFactoid("botsnack")

        # Verify we're at 2
        mood = self.db.mood()
        self.assertEqual(mood, 2, "After 2 snacks, mood is not 2")

        # 4 smacks...        
        self.db.getFactoid("botsmack")
        self.db.getFactoid("botsmack")
        self.db.getFactoid("botsmack")
        self.db.getFactoid("botsmack")

        # Now we should be at -2
        mood = self.db.mood()
        self.assertEqual(mood, -2, "After 4 smacks, mood is not -22")
        
    def tearDown(self):
        # Clear all factoids and history
        self.db.deleteAllFactoids()
        #print("Skipping factoid teardown")


class DbAccessTellTest(unittest.TestCase):
    missinguser = "somerandomuser"
    
    def setUp(self):
        config = configparser.ConfigParser()
        results = config.read('gthx.config.local')
        if not results:
            raise SystemExit("Failed to read config file 'gthx.config.local'")
        dbHost = config.get('MYSQL','GTHX_MYSQL_HOST')
        dbUser = config.get('MYSQL','GTHX_MYSQL_USER')
        dbPassword = config.get('MYSQL','GTHX_MYSQL_PASSWORD')
        dbName = config.get('MYSQL','GTHX_MYSQL_DATABASE')

        self.db = DbAccess(dbHost, dbUser, dbPassword, dbName)

    def test_user_with_no_tells(self):
        user="someuser"

        data = self.db.getTell(user)
        self.assertEqual(len(data), 0, "Wrong number of tells returned for a user who doesn't have any waiting")
        
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
        self.assertEqual(len(data), 1, "Got wrong number of tells for a user")
        
        tell = data[0]
        self.assertEqual(tell[1], teller, "Got wrong author for a tell")
        self.assertEqual(tell[2], receiver, "Got wrong recipient for a tell")
        self.assertEqual(tell[4], message, "Got wrong message for a tell")
        self.assertEqual(tell[5], kthxKnows, "Got wrong inTracked for a tell")

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
        self.assertEqual(len(data), 1, "Got wrong number of tells for a user")
        
        tell = data[0]
        self.assertEqual(tell[1], teller, "Got wrong author for a tell")
        self.assertEqual(tell[2], receiver, "Got wrong recipient for a tell")
        self.assertEqual(tell[4], message, "Got wrong message for a tell")
        self.assertEqual(tell[5], kthxKnows, "Got wrong inTracked for a tell")

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
        self.assertEqual(len(data), 3, "Got wrong number of tells for a user")
        
        tell = data[0]
        self.assertEqual(tell[1], teller, "Got wrong author for a tell")
        self.assertEqual(tell[2], receiver, "Got wrong recipient for a tell")
        self.assertEqual(tell[4], message, "Got wrong message for a tell")
        self.assertEqual(tell[5], kthxKnows, "Got wrong inTracked for a tell")

        delta = datetime.now() - tell[3]
        self.assertLess(delta.total_seconds(), 2, "Wrong time returned for a tell date set: delta is %d" % delta.total_seconds())

        tell = data[1]
        self.assertEqual(tell[1], teller2, "Got wrong author for a tell")
        self.assertEqual(tell[2], receiver, "Got wrong recipient for a tell")
        self.assertEqual(tell[4], message2, "Got wrong message for a tell")
        self.assertEqual(tell[5], kthxKnows2, "Got wrong inTracked for a tell")

        delta = datetime.now() - tell[3]
        self.assertLess(delta.total_seconds(), 2, "Wrong time returned for a tell date set: delta is %d" % delta.total_seconds())

        tell = data[2]
        self.assertEqual(tell[1], teller3, "Got wrong author for a tell")
        self.assertEqual(tell[2], receiver, "Got wrong recipient for a tell")
        self.assertEqual(tell[4], message3, "Got wrong message for a tell")
        self.assertEqual(tell[5], kthxKnows3, "Got wrong inTracked for a tell")

        delta = datetime.now() - tell[3]
        self.assertLess(delta.total_seconds(), 2, "Wrong time returned for a tell date set: delta is %d" % delta.total_seconds())

        # Now get again for the same user to make sure they've been cleared
        data = self.db.getTell(receiver)
        self.assertFalse(data, "Got tells for a user with none waiting")
    
    def tearDown(self):
        self.db.deleteAllTells()
    
class DbAccessThingiverseTest(unittest.TestCase):
    
    def setUp(self):
        config = configparser.ConfigParser()
        results = config.read('gthx.config.local')
        if not results:
            raise SystemExit("Failed to read config file 'gthx.config.local'")
        dbHost = config.get('MYSQL','GTHX_MYSQL_HOST')
        dbUser = config.get('MYSQL','GTHX_MYSQL_USER')
        dbPassword = config.get('MYSQL','GTHX_MYSQL_PASSWORD')
        dbName = config.get('MYSQL','GTHX_MYSQL_DATABASE')

        self.db = DbAccess(dbHost, dbUser, dbPassword, dbName)

    def test_thingiverse_refs(self):
        testItem = 1234
        testTitle = "The most wonderful thing in the world"
        
        rows = self.db.addThingiverseRef(testItem)
        self.assertEqual(len(rows), 1, "First thingiverse ref returned the wrong number of rows.")
        data = rows[0]
        self.assertEqual(data[0], 1, "First thingiverse ref returned wrong number of references.")
        self.assertIsNone(data[1], "First thingiverse ref returned a title when it shouldn't have.")

        rows = self.db.addThingiverseRef(testItem)
        self.assertEqual(len(rows), 1, "Second thingiverse ref returned the wrong number of rows.")
        data = rows[0]
        self.assertEqual(data[0], 2, "Second thingiverse ref returned wrong number of references.")
        self.assertIsNone(data[1], "Second thingiverse ref returned a title when it shouldn't have.")

        rows = self.db.addThingiverseRef(testItem)
        self.assertEqual(len(rows), 1, "Third thingiverse ref returned the wrong number of rows.")
        data = rows[0]
        self.assertEqual(data[0], 3, "Third thingiverse ref returned wrong number of references.")
        self.assertIsNone(data[1], "Third thingiverse ref returned a title when it shouldn't have.")

        self.db.addThingiverseTitle(testItem, testTitle)
        
        rows = self.db.addThingiverseRef(testItem)
        self.assertEqual(len(rows), 1, "Fourth thingiverse ref returned the wrong number of rows.")
        data = rows[0]
        self.assertEqual(data[0], 4, "Fourth thingiverse ref returned wrong number of references.")
        self.assertEqual(data[1], testTitle, "Fourth thingiverse ref returned the wrong title.")
        
    def tearDown(self):
        self.db.deleteAllThingiverseRefs()

class DbAccessYoutubeRefTest(unittest.TestCase):
    
    def setUp(self):
        config = configparser.ConfigParser()
        results = config.read('gthx.config.local')
        if not results:
            raise SystemExit("Failed to read config file 'gthx.config.local'")
        dbHost = config.get('MYSQL','GTHX_MYSQL_HOST')
        dbUser = config.get('MYSQL','GTHX_MYSQL_USER')
        dbPassword = config.get('MYSQL','GTHX_MYSQL_PASSWORD')
        dbName = config.get('MYSQL','GTHX_MYSQL_DATABASE')

        self.db = DbAccess(dbHost, dbUser, dbPassword, dbName)

    def test_youtube_refs(self):
        testItem = "I7nVrT00ST4"
        testTitle = "Pro Riders Laughing"
        
        # Verify that referencing an item the first time causes the ref count to
        # be set to 1
        rows = self.db.addYoutubeRef(testItem)
        self.assertEqual(len(rows), 1, "First youtube ref returned the wrong number of rows.")
        data = rows[0]
        self.assertEqual(data[0], 1, "First youtube ref returned wrong number of references.")
        self.assertIsNone(data[1], "First youtube ref returned a title when it shouldn't have.")

        rows = self.db.addYoutubeRef(testItem)
        self.assertEqual(len(rows), 1, "First youtube ref returned the wrong number of rows.")
        data = rows[0]
        self.assertEqual(data[0], 2, "Second youtube ref returned wrong number of references.")
        self.assertIsNone(data[1], "Second youtube ref returned a title when it shouldn't have.")

        self.db.addYoutubeTitle(testItem, testTitle)
        
        rows = self.db.addYoutubeRef(testItem)
        self.assertEqual(len(rows), 1, "First youtube ref returned the wrong number of rows.")
        data = rows[0]
        self.assertEqual(data[0], 3, "Third youtube ref returned wrong number of references.")
        self.assertEqual(data[1], testTitle, "Third youtube ref returned the wrong title: '%s'" % data[1])
        
    def tearDown(self):
        self.db.deleteAllYoutubeRefs()
        #print "Skipping youtubeRefs teardown"

if __name__ == '__main__':
    unittest.main()
    
