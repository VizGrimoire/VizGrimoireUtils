#!/bin/bash

# where the scripts are located
export SCRIPTS_PATH="${SCRIPTS_PATH:-/vagrant/scripts}"

# server hostname
export HOSTNAME="$(hostname -f)"

# util scripts path
export UTILS_PATH="${SCRIPTS_PATH}/util"

# interface for the public ip
export IFACE="${IFACE:-eth1}"

# default password for mysql root user
export ROOT_DBPASSWD="rootpw"

# user and password for github
export GITHUB_USER=""
export GITHUB_PASSWD=""

### dashboard related variables
export DASH_HOSTNAME="dash.${HOSTNAME}"
export DASH_URL="http://${DASH_HOSTNAME}/browser"
export DASH_USER="automator"