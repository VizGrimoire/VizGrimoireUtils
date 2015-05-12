#!/bin/bash

# create user chanchan
adduser --disabled-password --gecos "automator" automator

# allow passwordless sudo
adduser automator sudo
cat <<EOF > /etc/sudoers.d/automator
automator ALL=(ALL) NOPASSWD:ALL
EOF
chmod 0440 /etc/sudoers.d/automator
