#!/bin/bash

su - ${DASH_USER} << EOF
cd Automator
sed -i tests/Test/conf/main.conf \
    -e "s/db_password =[ ]*$/db_password = rootpw/"
EOF