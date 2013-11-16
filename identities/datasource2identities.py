#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (C) 2012-2013 Bitergia
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
#       Daniel Izquierdo-Cortazar <dizquierdo@bitergia.com>
#       Alvaro del Castillo <acs@bitergia.com>

#
# datasource2identities.py
#
# This script is based on the outcomes of unifypeople.py used in the CVSAnalY
# database. This checks information about name and email FROM the email
# accounts # found in the people information in the data source.
# If this is found, then the table people_upeople is populated
# with the upeople_id found in identities.
# If not, a new entry in identities table is generated and its associated link
# to the people_upeople table.

import MySQLdb
import _mysql_exceptions
from optparse import OptionParser
import sys


def getOptions():
    parser = OptionParser(usage='Usage: %prog [options]',
                          description='Detect and unify unique identities ' +
                                      'for VizGrimoire Data Sources',
                          version='0.1')
    parser.add_option('--data-source', dest='data_source',
                      help='Data Source to be used (its, mls, irc, mediawiki)',
                      default=None)
    parser.add_option('--db-name-ds', dest='db_name_ds',
                      help='Data source database name', default=None)
    parser.add_option('--db-name-ids', dest='db_name_ids',
                      help='Identities database name', default=None)
    parser.add_option('-u', '--db-user', dest='db_user',
                      help='Database user name', default='root')
    parser.add_option('-p', '--db-password', dest='db_password',
                      help='Database user password', default='')
    parser.add_option('--db-hostname', dest='db_hostname',
                      help='Name of the host WHERE database server is running',
                      default='localhost')
    parser.add_option('--db-port', dest='db_port',
                      help='Port of the host WHERE database server is running',
                      default='3306')

    (ops, args) = parser.parse_args()

    if len(args) != 0:
        parser.error("Wrong number of arguments")

    if not(ops.data_source and ops.db_name_ds and ops.db_user
           and ops.db_name_ids):
        parser.error("--db-name-ds --db-name-ids --db-user" +
                     "and --data-source are needed")
    return ops


def connect(db, cfg):
    user = cfg.db_user
    password = cfg.db_password
    host = cfg.db_hostname

    try:
        db = MySQLdb.connect(user=user, passwd=password, db=db, charset='utf8')
        return db, db.cursor()
    except:
        print("Database connection error")
        raise


def execute_query(connector, query):
    results = int(connector.execute(query))
    if results > 0:
        result1 = connector.fetchall()
        return result1
    else:
        return []


def create_tables(db, connector):
    connector.execute("DROP TABLE IF EXISTS people_upeople")
    connector.execute("""CREATE TABLE people_upeople (
                               people_id varchar(255) NOT NULL,
                               upeople_id int(11) NOT NULL,
                               PRIMARY KEY (people_id)
                  ) ENGINE=MyISAM DEFAULT CHARSET=utf8""")
    query = "CREATE INDEX pup_upid ON people_upeople (upeople_id)"
    connector.execute(query)
    connector.execute("ALTER TABLE people_upeople DISABLE KEYS")
    db.commit()

    return


def insert_identity(cursor_ids, upeople_id, field, field_type):
    if (len(search_identity(cursor_ids, field)) > 0):
        return
    query = "INSERT INTO identities (upeople_id, identity, type)" + \
            "VALUES (%s, %s, %s)"
    cursor_ids.execute(query, (upeople_id, field, field_type))

def insert_upeople(cursor_ids, cursor_ds, people_id, field, field_type):
    # Insert in people_upeople, identities and upeople (new identitiy)

    # Max (upeople_)id FROM upeople table
    query = "SELECT MAX(id) FROM upeople;"
    results = execute_query(cursor_ids, query)
    upeople_id = int(results[0][0]) + 1

    query = "INSERT INTO upeople (id, identifier) VALUES (%s, %s)"
    cursor_ids.execute(query, (upeople_id, field))

    insert_identity(cursor_ids, upeople_id, field, field_type)

    reuse_identity(cursor_ds, people_id, upeople_id)

    return upeople_id


def search_identity(cursor_ids, field):
    query = "SELECT upeople_id FROM identities WHERE identity = %s"
    results = int(cursor_ids.execute(query, (field)))
    if results > 0:
        return cursor_ids.fetchall()
    else:
        return []


def reuse_identity(cursor_ds, people_id, upeople_id):
    query = "INSERT INTO people_upeople (people_id, upeople_id) "
    query += "VALUES (%s, %s)"
    try:
        cursor_ds.execute(query, (people_id, upeople_id))
    except _mysql_exceptions.IntegrityError:
        print (str(people_id) + " to " + str(upeople_id) +
               " already exits")


def process_identity(cursor_ids, cursor_ds, people_id, field, field_type):
    global reusedids, newids
    results_ids = search_identity(cursor_ids, field)
    if len(results_ids) > 0:
        upeople_id = int(results_ids[0][0])
        print ("Reusing identity by " + field_type + " "
               + field).encode('utf-8')
        reuse_identity(cursor_ds, people_id, upeople_id)
        reusedids += 1
    else:
        upeople_id = insert_upeople(cursor_ids, cursor_ds, people_id,
                                    field, field_type)
        newids += 1
    return upeople_id


def main():
    global reusedids, newids

    cfg = getOptions()
    data_source = cfg.data_source
    db_database_ds, cursor_ds = connect(cfg.db_name_ds, cfg)
    db_ids, cursor_ids = connect(cfg.db_name_ids, cfg)

    create_tables(db_database_ds, cursor_ds)
    if (data_source == "its" or data_source == "scr"):
        query = "SELECT id, name, email, user_id FROM people"
    elif (data_source == "mls"):
        query = "SELECT name, email_address FROM people"
    elif (data_source == "irc"):
        query = "SELECT DISTINCT(nick) FROM irclog"
    elif (data_source == "mediawiki"):
        query = "SELECT DISTINCT(user) FROM wiki_pages_revs"
    else:
        print ("Data source " + data_source + " not supported.")
        return
    results = execute_query(cursor_ds, query)
    total = len(results)
    print ("Total identities to analyze: " + str(total))

    for result in results:
        if (data_source == "irc" or data_source == "mediawiki"):
            name = result[0]
            people_id = name
            email = user_id = None
        elif (data_source == "mls"):
            name = result[0]
            email = result[1]
            people_id = email
            user_id = None
        else:
            people_id = int(result[0])
            name = result[1]
            email = result[2]
            user_id = result[3]

        upeople_id = None

        if name != '' and name is not None and name != 'None':
            if (upeople_id):
                insert_identity(cursor_ids, upeople_id, name, "name")
            else:
                upeople_id = process_identity(cursor_ids, cursor_ds,
                                              people_id, name, "name")
        if email != '' and email is not None and email != 'None':
            if (upeople_id):
                insert_identity(cursor_ids, upeople_id, email, "email")
            else:
                upeople_id = process_identity(cursor_ids, cursor_ds,
                                              people_id, email, "email")
        if user_id != '' and user_id is not None and user_id != 'None':
            if (upeople_id):
                insert_identity(cursor_ids, upeople_id, user_id, "user_id")
            else:
                upeople_id = process_identity(cursor_ids, cursor_ds,
                                              people_id, user_id, "user_id")

    db_ids.commit()
    db_database_ds.commit()

    print ("Total analyzed: " + str(total))
    print ("New identities: " + str(newids))
    print ("Reused identities: " + str(reusedids))
    return

if __name__ == "__main__":
    # Global vars
    newids = reusedids = 0
    main()
