CREATE TABLE `factoid_history` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `item` varchar(255) DEFAULT NULL,
  `value` varchar(512) DEFAULT NULL,
  `nick` varchar(30) DEFAULT NULL,
  `dateset` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
);

CREATE TABLE `factoids` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `item` varchar(255) DEFAULT NULL,
  `are` tinyint(1) DEFAULT NULL,
  `value` varchar(512) DEFAULT NULL,
  `nick` varchar(30) DEFAULT NULL,
  `dateset` datetime DEFAULT NULL,
  `locked` tinyint(1) DEFAULT NULL,
  `lastsync` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
);

CREATE TABLE `seen` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(30) DEFAULT NULL,
  `channel` varchar(30) DEFAULT NULL,
  `timestamp` datetime DEFAULT NULL,
  `message` varchar(512) DEFAULT NULL,
  PRIMARY KEY (`id`)
);

CREATE TABLE `tell` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `author` varchar(60) DEFAULT NULL,
  `recipient` varchar(60) DEFAULT NULL,
  `timestamp` datetime DEFAULT NULL,
  `message` text,
  `inTracked` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`id`)
);

CREATE TABLE `version` (
  `version` int(11) NOT NULL,
  `timestamp` datetime DEFAULT NULL
);

INSERT INTO version (version, timestamp) VALUES (2, CURRENT_TIMESTAMP);

CREATE TABLE `refs` (
  `id` int(11) NOT NULL,
  `count` int(11) NOT NULL,
  `lastreferenced` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
);

# Missing a trigger that the current DbAccess requires!!
# (But maybe we don't want it and should just change DbAccess so it's not required)
# mysql> show triggers in gthx;
# +---------------+--------+----------+-----------------------------------------------------------------------------------------------------------------------------+--------+---------+----------+----------------+----------------------+----------------------+--------------------+
#| Trigger       | Event  | Table    | Statement                                                                                                                   | Timing | Created | sql_mode | Definer        | character_set_client | collation_connection | Database Collation |
#+---------------+--------+----------+-----------------------------------------------------------------------------------------------------------------------------+--------+---------+----------+----------------+----------------------+----------------------+--------------------+
#| insertfactoid | INSERT | factoids | BEGIN
    INSERT INTO factoid_history SET item = NEW.item, value = NEW.value, nick = NEW.nick, dateset = NEW.dateset;
      END | BEFORE | NULL    |          | gthx@localhost | utf8                 | utf8_general_ci      | latin1_swedish_ci  |
#+---------------+--------+----------+-----------------------------------------------------------------------------------------------------------------------------+--------+---------+----------+----------------+----------------------+----------------------+--------------------+
#      1 row in set (0.00 sec)
