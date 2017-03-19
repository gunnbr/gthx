#!/bin/bash
echo -n Stopping gthx service...
sudo systemctl stop gthx
echo Done.
sudo cp gthx.service /lib/systemd/system/gthx.service
sudo mkdir -p /etc/gthx
sudo cp gthx.config.local /etc/gthx/gthx.config
sudo chown www-data /etc/gthx/gthx.config
sudo chgrp www-data /etc/gthx/gthx.config
sudo chmod 640 /etc/gthx/gthx.config
sudo systemctl daemon-reload
sudo mkdir -p /usr/sbin/gthx
sudo cp gthx.py /usr/sbin/gthx/
sudo cp DbAccess.py /usr/sbin/gthx/
sudo cp Email.py /usr/sbin/gthx/
echo -n Starting gthx service...
sudo systemctl start gthx
echo Done.
