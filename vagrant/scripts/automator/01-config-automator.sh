#!/bin/bash

su - ${DASH_USER} << EOF
cd Automator
sed -i tests/Test/conf/main.conf \
    -e "s/db_password =[ ]*$/db_password = rootpw/" \
    -e "s/\[gerrit\]/\[gerrit_off\]/" \
    -e "s/^db_gerrit/#db_gerrit/"
EOF