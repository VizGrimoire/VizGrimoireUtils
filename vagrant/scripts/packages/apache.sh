#!/bin/bash

# install packages
apt-get install -qy apache2

# enable modules
a2enmod ssl

# disable default site
a2dissite 000-default

# restart service
service apache2 restart
