
# Important to have the DB set to the "real" utf8 character set.
# CREATE DATABASE gthx CHARACTER SET = 'utf8mb4' COLLATE = 'utf8mb4_unicode_ci';
# TODO:
#   Change name timestamp in seen and tell tables to something else since timestamp is a different type

CREATE TABLE `factoid_history` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `item` varchar(255) DEFAULT NULL,
  `value` varchar(512) DEFAULT NULL,
  `nick` varchar(30) DEFAULT NULL,
  `dateset` datetime(6) DEFAULT NULL,
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

# Add locked botsnack and botsmack factoids?

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

CREATE TABLE `refs` (
  `item` varchar(255) NOT NULL,
  `count` int(11) NOT NULL,
  `lastreferenced` datetime DEFAULT NULL,
  PRIMARY KEY (`item`)
);

CREATE TABLE `thingiverseRefs` (
  `item` int(11) NOT NULL,
  `title` varchar(255) DEFAULT NULL,
  `count` int(11) NOT NULL,
  `lastreferenced` datetime DEFAULT NULL,
  PRIMARY KEY (`item`)
);

CREATE TABLE `youtubeRefs` (
  `item` varchar(255) NOT NULL,
  `title` varchar(255) DEFAULT NULL,
  `count` int(11) NOT NULL,
  `lastreferenced` datetime DEFAULT NULL,
  PRIMARY KEY (`item`)
);

CREATE TABLE `version` (
  `version` int(11) NOT NULL,
  `timestamp` datetime DEFAULT NULL
);

INSERT INTO version (version, timestamp) VALUES (5, CURRENT_TIMESTAMP);
