#!/bin/bash

su - ${DASH_USER} << EOF
cd Automator
./launch.py -d /home/automator/Automator/tests/Test
cd /home/automator/Automator/tests/Test/tools/VizGrimoireJS
make
EOF

rm /var/www/browser
ln -s /home/automator/Automator/tests/Test/tools/VizGrimoireJS/browser /var/www/
