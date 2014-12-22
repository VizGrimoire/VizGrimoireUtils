#!/bin/bash

su - ${DASH_USER} << EOF
rm -rf Automator
git clone https://github.com/MetricsGrimoire/Automator.git
EOF
