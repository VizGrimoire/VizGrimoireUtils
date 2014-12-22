#!/bin/bash

R_REPO="http://cran.us.r-project.org"

cat << EOF > R.packages
install.packages('RMySQL',repos='${R_REPO}')
install.packages('rjson',repos='${R_REPO}')
install.packages('RColorBrewer',repos='${R_REPO}')
install.packages('ggplot2',repos='${R_REPO}')
install.packages('rgl',repos='${R_REPO}')
install.packages('optparse',repos='${R_REPO}')
install.packages('ISOweek',repos='${R_REPO}')
install.packages('zoo',repos='${R_REPO}')
EOF

R '--vanilla' < R.packages

rm R.packages