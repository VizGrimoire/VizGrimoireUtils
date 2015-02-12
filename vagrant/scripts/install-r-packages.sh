#!/bin/bash

R_REPO="http://cran.us.r-project.org"

cat << EOF > R.packages
install.packages('RMySQL',repos='${R_REPO}')
install.packages('RColorBrewer',repos='${R_REPO}')
install.packages('ggplot2',repos='${R_REPO}')
install.packages('rgl',repos='${R_REPO}')
install.packages('optparse',repos='${R_REPO}')
install.packages('ISOweek',repos='${R_REPO}')
install.packages('zoo',repos='${R_REPO}')
EOF
# install.packages('rjson',repos='${R_REPO}') not exists for R 3.0.2 from Ubuntu

R '--vanilla' < R.packages
rm R.packages

# rjson
wget http://cran.rstudio.com/src/contrib/Archive/rjson/rjson_0.2.13.tar.gz
R CMD INSTALL rjson_0.2.13.tar.gz
rm rjson_0.2.13.tar.gz

