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

import logging
import MySQLdb, _mysql_exceptions
from optparse import OptionParser
import re


def getOptions():
    parser = OptionParser(usage='Usage: %prog [options]',
                          description='Detect and unify unique identities ' +
                                      'for VizGrimoire Data Sources',
                          version='0.1')
    parser.add_option('--data-source', dest='data_source',
                      help='Data Source to be used (its, mls, irc, mediawiki, releases, qaforums)',
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
        logging.error("Database connection error")
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
    if field != '' and field is not None and field != 'None':
        if (len(search_identity(cursor_ids, field, field_type)) > 0):
            return
        query = "INSERT INTO identities (upeople_id, identity, type)" + \
                "VALUES (%s, %s, %s)"
        cursor_ids.execute(query, (upeople_id, field, field_type))

def insert_upeople(cursor_ids, cursor_ds, people_id, field, field_type):
    # Insert in people_upeople, identities and upeople (new identitiy)
    if not (field != '' and field is not None and field != 'None'):
        return None

    # Max (upeople_)id FROM upeople table
    query = "SELECT MAX(id) FROM upeople;"
    results = execute_query(cursor_ids, query)
    last_id = results[0][0]
    if last_id is None: last_id = 0
    upeople_id = int(last_id)
    upeople_id += 1

    query = "INSERT INTO upeople (id, identifier) VALUES (%s, %s)"
    cursor_ids.execute(query, (upeople_id, field))

    insert_identity(cursor_ids, upeople_id, field, field_type)

    insert_people_upeople(cursor_ds, people_id, upeople_id)

    return upeople_id

def insert_people_upeople(cursor_ds, people_id, upeople_id):
    query = "INSERT INTO people_upeople (people_id, upeople_id) "
    query += "VALUES (%s, %s)"
    try:
        cursor_ds.execute(query, (people_id, upeople_id))
    except _mysql_exceptions.IntegrityError:
        # logging.info(str(people_id) + " to " + str(upeople_id) + " already exits")
        pass

def search_identity(cursor_ids, field, field_type):
    query = "SELECT upeople_id FROM identities WHERE identity = %s AND type=%s"
    results = int(cursor_ids.execute(query, (field, field_type)))
    if results > 0:
        return cursor_ids.fetchall()
    else:
        return []

def main():
    global reusedids, newids

    supported_data_sources = ["its","its_1","scr","pullpo","mls","irc","mediawiki","releases","qaforums"]

    logging.basicConfig(level=logging.INFO,format='%(asctime)s %(message)s')

    cfg = getOptions()
    data_source = cfg.data_source

    if data_source not in supported_data_sources:
        logging.info ("Data source " + data_source + " not supported.")
        return

    db_database_ds, cursor_ds = connect(cfg.db_name_ds, cfg)
    db_ids, cursor_ids = connect(cfg.db_name_ids, cfg)

    create_tables(db_database_ds, cursor_ds)
    if (data_source == "its" or data_source == "its_1" or data_source == "scr"):
        query = "SELECT id, name, email, user_id FROM people"
    elif (data_source == "mls"):
        query = "SELECT name, email_address FROM people"
    elif (data_source == "irc"):
        query = "SELECT DISTINCT(nick) FROM irclog"
    elif (data_source == "mediawiki"):
        query = "SELECT DISTINCT(user) FROM wiki_pages_revs"
    elif (data_source == "releases"):
        query = "SELECT id, username, email FROM users"
    elif (data_source == "qaforums"):
        query = "SELECT id, username, email FROM people"
    elif (data_source == "pullpo"):
        query = "SELECT id, login, email FROM people"
    else:
        return
    results = execute_query(cursor_ds, query)
    total = len(results)
    logging.info ("Generating unique identities for " + data_source)
    logging.info (" Total identities to analyze: " + str(total))

    # people_id used for main identifier for upeople
    for result in results:
        if data_source in ['irc','mediawiki']:
            name = result[0]
            people_id = user_id = name
            email = None
        elif data_source in ['releases', 'qaforums']:
            people_id = int(result[0])
            name = result[1]
            email = result[2]
            user_id = result[1]
        elif (data_source == "mls"):
            name = result[0]
            email = result[1]
            people_id = email
            user_id = None
        elif (data_source == "pullpo"):
            people_id = result[0]
            name = user_id = result[1]
            email = result[2]
        elif (data_source == "its" or data_source == "its_1" or data_source == "scr"):
            people_id = int(result[0])
            name = result[1]
            email = result[2]
            user_id = result[3]
        else:
            people_id = int(result[0])
            user_id = name = result[1]
            email = None

        upeople_id = None

        # Try to find the upeople using all identifiers
        # If upeople is not found create the new identity
        # We use the email field available in all data sources as the main identifier
        for field_type in  ['name','email','user_id']:
            if field_type == 'email': field = email
            elif field_type == 'name':
                field = name
                if field is None: continue
                # For name, at least first and family
                # \s: any whitespace character \w: any alphanumeric character and the underscore
                if not re.match(r"\w+\s\w+", field): continue
            elif field_type == 'user_id': field = user_id
            if field != '' and field is not None and field != 'None':
                results_ids = search_identity(cursor_ids, field, field_type)
                if len(results_ids) > 0:
                    upeople_id = int(results_ids[0][0])

        if upeople_id is None:
            upeople_id = insert_upeople(cursor_ids, cursor_ds, people_id,
                                        email, "email")
            if upeople_id is None:
                upeople_id = insert_upeople(cursor_ids, cursor_ds, people_id,
                                            user_id, "user_id")
            if upeople_id is None:
                if name is not None:
                    if re.match(r"\w+\s\w+", name):
                        upeople_id = insert_upeople(cursor_ids, cursor_ds, people_id,
                                                name, "name")
            if upeople_id is None:
                logging.error("Can't register %s %s %s" % (email, name, user_id))
                continue
            newids += 1
        else:
            # The empty people_upeople table should be populated
            insert_people_upeople(cursor_ds, people_id, upeople_id)
            reusedids += 1

        # We have now the upeople_id, but we don't now with which field.
        # Try to insert all fields and in insert_identity if already do nothing
        insert_identity(cursor_ids, upeople_id, email, "email")
        insert_identity(cursor_ids, upeople_id, user_id, "user_id")
        # Just insert identifiers with a correct format for name
        if name is not None:
            if re.match(r"\w+\s\w+", name):
                insert_identity(cursor_ids, upeople_id, name, "name")

    db_ids.commit()
    db_database_ds.commit()

    logging.info (" Total analyzed: " + str(total))
    logging.info (" New identities: " + str(newids))
    logging.info (" Reused identities: " + str(reusedids))
    return

if __name__ == "__main__":
    # Global vars
    newids = reusedids = 0
    main()
