#!/bin/bash

export DEBIAN_FRONTEND=noninteractive

apt update
apt upgrade -y
apt-get install --no-install-recommends -y git python3-pip

# install systemd service
cp hedgcoxekhav.service /lib/systemd/system/

# install/update software from github
rm -rf /var/lib/hedgcoxekhav
cd /var/lib
git clone https://github.com/jgruber/hedgcoxekhav.git
cd /var/lib/hedgcoxekhav
pip3 install -r requirements.txt
chmod +x /var/lib/hedgcoxekhav/avswitcher.py

# enable / start service
systemctl enable hedgcoxekhav.service
systemctl start hedgcoxekhav.service

