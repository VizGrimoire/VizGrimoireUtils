#!/bin/bash

# Configure Automator to work with github projects
# SCM
# Tickets
# Pull Requests
# Others
su - ${DASH_USER} << EOF
cd Automator

sed -i tests/Test/conf/main.conf \
    -e "s/\[gerrit\]/\[gerrit_off\]/" \
    -e "s/^db_gerrit/#db_gerrit/"
    -e "s/\[irc\]/\[irc_off\]/" \
    -e "s/^db_irc/#db_gerrit/"
    -e "s/\[mediawiki\]/\[mediawiki_off\]/"
    -e "s/^db_mediawiki/#db_gerrit/"
EOF