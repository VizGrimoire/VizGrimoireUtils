#!/bin/bash

su - ${DASH_USER} << EOF
cd Automator
sed -i tests/Test/conf/main.conf \
    -e "s/db_password = /db_password = rootpw/"


./launch.py -d /home/automator/Automator/tests/Test
cd /home/automator/Automator/tests/Test/tools/VizGrimoireJS
make
EOF

ln -s /home/automator/Automator/tests/Test/tools/VizGrimoireJS/browser /var/www/