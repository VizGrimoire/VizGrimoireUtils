#!/bin/bash

exit 0

su - ${DASH_USER} << EOF

rm -rf Automator
git clone https://github.com/MetricsGrimoire/Automator.git
cd Automator
./create_projects.py -p tests/automator_test.conf -d tests -s -n Test  --dbuser=root --dbpasswd=rootpw

EOF