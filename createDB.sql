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

INSERT INTO version (version, timestamp) VALUES (1, CURRENT_TIMESTAMP);

