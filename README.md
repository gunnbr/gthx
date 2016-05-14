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
* MySQL (gthx was developed on version 5.5)
* Python 2.7
* Twisted (Python library)

### Create a new database
Once that is done, create a new database and user in MySQL for gthx to use and grant the user full permissions
on that database. Something like:

```
create database gthx;
grant all on gthx.* to 'gthxuser' identified by 'password';
```

Run the gthx DB install script:
```
mysql -u gthxuser -p[password] [database_name] < createDB.sql
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

Copy the upstart script `gthx-upstart` to `gthx-upstart.local`.

Edit `gthx-upstart.local` to configure everything.

Run `install.sh` to copy the gthx to /usr/sbin/gthx and the upstart script to /etc/init.

Run `sudo service gthx start` to start gthx. (The upstart script can, of course, be changed to match the name of your bot.)



