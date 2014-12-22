#!/bin/bash

su - ${DASH_USER} << EOF
rm -rf Automator
git clone https://github.com/MetricsGrimoire/Automator.git
cd Automator
./create_projects.py -p tests/automator_test.conf -d tests -s -n Test
./launch.py -d /home/automator/Automator/tests/Test
cd /home/automator/Automator/tests/Test/tools/VizGrimoireJS
make
EOF

ln -s /home/automator/Automator/tests/Test/tools/VizGrimoireJS/browser /var/www/