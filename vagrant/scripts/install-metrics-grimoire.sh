#!/bin/bash

su - ${DASH_USER} << EOF

rm -rf metrics_grimoire
mkdir metrics_grimoire
cd metrics_grimoire

git clone https://github.com/MetricsGrimoire/RepositoryHandler.git
git clone https://github.com/MetricsGrimoire/CVSAnalY.git
git clone https://github.com/MetricsGrimoire/Bicho.git
git clone https://github.com/MetricsGrimoire/MailingListStats.git
cd  MailingListStats
git checkout c6658738845471f6629aff4c84b96b0e3db8437d
cd ..
git clone https://github.com/MetricsGrimoire/IRCAnalysis.git
git clone https://github.com/MetricsGrimoire/Octopus.git
git clone https://github.com/MetricsGrimoire/Sibyl.git
git clone https://github.com/MetricsGrimoire/MediaWikiAnalysis.git
	
EOF

su - ${DASH_USER} -c 'cd metrics_grimoire; for i in `ls`; do cd $i; echo `pwd`; sudo python setup.py install; cd ..; done'

