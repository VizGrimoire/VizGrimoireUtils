#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (C) 2012 Bitergia
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
#       Alvaro del Castillo <acs@bitergia.com>

#
# domains_analysis.py
#
# This scripts is based on the outcomes of unifypeople.py.
# This will provide two tables: domains and upeople_domains


import MySQLdb
import hashlib, logging, sys
from optparse import OptionGroup, OptionParser


def connect(cfg):
    user = cfg.db_user
    password = cfg.db_password
    host = cfg.db_hostname
    db = cfg.db_database

    try:
        db = MySQLdb.connect(user = user, passwd = password, db = db)
        return db
    except:
        logging.error("Database connection error")
    raise

# From GrimoireSQL
def execute_query (cursor, sql):
    result = {}
    cursor.execute(sql)
    rows = cursor.rowcount
    columns = cursor.description

    for column in columns:
        result[column[0]] = []
    if rows > 1:
        for value in cursor.fetchall():
            for (index,column) in enumerate(value):
                result[columns[index][0]].append(column)
    elif rows == 1:
        value = cursor.fetchone()
        for i in range (0, len(columns)):
            result[columns[i][0]] = value[i]
    return result

def getOptions():
    parser = OptionParser(usage='Usage: %prog [options]', 
                          description='Anonymize a field in a table',
                          version='0.1')

    parser.add_option('-d', '--db-database', dest='db_database',
                     help='Output database name', default=None)
    parser.add_option('-u','--db-user', dest='db_user',
                     help='Database user name', default='root')
    parser.add_option('-p', '--db-password', dest='db_password',
                     help='Database user password', default='')
    parser.add_option('--db-hostname', dest='db_hostname',
                     help='Name of the host where database server is running',
                     default='localhost')
    parser.add_option('--db-port', dest='db_port',
                     help='Port of the host where database server is running',
                     default='3306')
    parser.add_option('--db-table', dest='db_table',
                     help='Table with the fields to be anonymized')
    parser.add_option('--db-field', dest='db_field',
                     help='Fields to be anonymized')
    (opts, args) = parser.parse_args()

    if len(args) != 0:
        parser.error("Arguments should be passed as - or -- options")

    if (not opts.db_table or not opts.db_field):
        parser.error("table and field are needed")

    return opts

def anonymize_field (cursor, table, field):
    logging.info('Anonymazing %s from %s' % (field, table))
    q = "SELECT DISTINCT(%s) from %s" % (field, table)
    anon_list = execute_query(cursor, q)
    total = len(anon_list[field])
    done = 0
    for data in anon_list[field]:
        if done % 100 == 0: logging.info ("Pending %i ", total-done)
        anon_data = hashlib.md5(data).hexdigest()
        q = "UPDATE %s SET %s = '%s' WHERE %s = '%s'" % (table, field, anon_data, field, data)
        cursor.execute(q)
        done += 1

def main():
    logging.basicConfig(level=logging.INFO,format='%(asctime)s %(message)s')

    opts = getOptions()
    db = connect(opts)
    cursor = db.cursor()
    anonymize_field (cursor, opts.db_table, opts.db_field)

if __name__ == '__main__':
    main()