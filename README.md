# gthx
Gthx is an IRC bot that tracks the status of another bot and takes over when the primary bot is down.

Gthx is written to handle the same commands that [drupal bot](https://www.drupal.org/project/bot) does.
It also monitors the factoids and "tells"
sent to the bot being tracked to keep its own database up to date. When the tracked bot is gone, gthx automatically
replies to factoids and relays the tells.

## History
Gthx was originally written for #reprap where their main bot, "kthx" crashed often due to bugs in
[drupal bot](https://www.drupal.org/project/bot), most notably handling of emoji.

I was looking for an excuse to do a bigger project in python, so that's why I chose it. As is clear
from the code, I'm far from a python expert and welcome any fixes or changes to make things more
"pythony".

## Installation
To install a new bot, make sure you already have installed:
* MySQL or MariaDB
* libmysqlclient-dev
* Python 2.7

### Install required Python libraries
The currently required libraries are:
* MySQLdb (Python library "mysqldb")
* Twisted (Python library)
To install these automatically, run:
```
pip install -r reuirements.txt
```

### Create a new database
Once that is done, create a new database and user in MySQL for gthx to use and grant the user full permissions
on that database. Something like:

```
create database gthx;
grant all on gthx.* to 'gthxuser' identified by 'password';
```

Run the gthx DB install script:
```
mysql -u gthxuser -p [database_name] < createDB.sql
```
### Backup and restore an existing database
One way to backup an existing gthx DB is by using mysqldump:
```
mysqldump -u gthxuser -p[password] [database_name] > backup_filename.sql
```

This backup file can then be restored (on the same or a different machine) with:
```
mysql -u root -p[root_password] [database_name] < backup_filename.sql
```

## Configuring to run at system boot

### systemd (Ubuntu 16.04 and beyond)
Copy the configuration file `gthx.config` to `gthx.config.local`

Edit `gthx.config.local` to configure everything.

Run `install.sh` to copy gthx to /usr/sbin/gthx and the config file to /etc/gthx.
This also uses systemctl to stop the service if it's running and reload all information, then restart
the service.

gthx is now configured to run at startup.

### Upstart (Ubuntu 14.04 and below)
(WARNING: This section is out of date)
Copy the upstart script `gthx-upstart` to `gthx-upstart.local`.

Edit `gthx-upstart.local` to configure everything.

~~Run `install.sh` to copy the gthx to /usr/sbin/gthx and the upstart script to /etc/init.~~
**install.sh has been modified to only work with systemd at the moment. To use upstart, please use an
older version of install.sh. I'll restore this file to install-upstart.sh at some point in the future.**

Run `sudo service gthx start` to start gthx. (The upstart script can, of course, be changed to match the name of your bot.)

## Running the unit tests
To run the unit tests:
* Create a fresh DB and possibly user
* Put the user and DB information in `gthx.config.local`
* Run `python test.py`


