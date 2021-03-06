# Copyright (C) 2014 Bitergia
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
# Authors :
#       Daniel Izquierdo Cortazar <dizquierdo@bitergia.com>


# $1: output dir
# $2: URL user
# $3: URL password
# $4: URL
# $5: database user
# $6: database


# Download of logs
wget -N -H -r --level=1 -k -np -P $1 -nd --user=$2 --password=$3 $4

# List of files to be parsed
files=`ls $1/*Weekly*.csv`

# Dropping previous versions
mysql -u $5 -D $6 -e "delete from downloads"

# Inserting all csv files into database
for file in $files
do
 mysql -u $5 -D $6 --local-infile  -e "load data local infile '`echo $file`' into table downloads fields terminated by ',' enclosed by '\\\"' lines terminated by '\n' (date, ip, package, protocol)"
done

