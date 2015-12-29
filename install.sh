#!/bin/bash
sudo cp gthx-upstart.local /etc/init/gthx.conf
sudo mkdir -p /usr/sbin/gthx
sudo cp gthx.py /usr/sbin/gthx/
sudo cp DbAccess.py /usr/sbin/gthx/
sudo cp Email.py /usr/sbin/gthx/
