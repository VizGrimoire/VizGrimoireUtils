#!/bin/bash

# check distribution
DIST=""
if [ -f "/etc/lsb-release" ]; then
    grep -q "Ubuntu 14.04" "/etc/lsb-release" && DIST="ubuntu14.04"
else
    if [ -f "/etc/debian_version" ]; then
        grep -q "7" "/etc/debian_version" && DIST="debian7"
    fi
fi

case ${DIST} in
    "debian7")
	echo "Debian 7 provisioning for Grimoire is not supported yet"
    exit 1
	;;
    "ubuntu14.04")
	echo "Provisioning Grimoire for Ubuntu 14.04."
	;;
    *)
	echo "Unsupported distribution"
	exit 1
	;;
esac
export DIST

# allow running the provision scripts on non-vagrant environments
_vagrant_user="vagrant"
getent passwd ${_vagrant_user} 2>&1 >/dev/null
_status=$?
case ${_status} in
    0)
	# running on vagrant
	SCRIPTS_PATH="/vagrant/scripts"
	# when using vagrant, the public IP will be on eth1
	IFACE="eth1"
	;;
    2)
	# vagrant user not found
	SC_PATH=$( cd $( dirname $0 ) 2>&1 >/dev/null && pwd )
	mkdir -p /opt/vagrant && cp -r ${SC_PATH} /opt/vagrant
	SCRIPTS_PATH="/opt/vagrant/scripts"
	# use the default interface for the public IP
	IFACE="eth0"
	;;
    *)
	# it should not get here
	echo "getent failed with error: ${_status}"
	exit 1
	;;
esac

cd ${SCRIPTS_PATH}

# load environment variables
source variables.sh

# swap: 512 MB default
bash swap.sh

# load packages
bash packages.sh

# install all R packages
bash install-r-packages.sh

# create main user for install and execution
bash setup-user.sh

# install MetricsGrimoire
bash install-metrics-grimoire.sh

# install Automator (GrimoireLib+VizGrimoire)
bash automator.sh

# clean package cache
apt-get -qy clean