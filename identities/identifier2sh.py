#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (C) 2015 Bitergia

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.
#
# Author: Alvaro del Castillo <acs@bitergia.com>

# This script completes the uidentities.identifier field in a SortingHat db

from optparse import OptionParser
import logging, MySQLdb, sys, random

def open_database(myuser, mypassword, mydb):
    con = MySQLdb.Connect(host="127.0.0.1",
                          port=3306,
                          user=myuser,
                          passwd=mypassword,
                          db=mydb)
    # cursor = con.cursor()
    # return cursor
    return con


def close_database(con):
    con.close()


def read_options():
    parser = OptionParser(usage="usage: %prog [options]",
                          version="%prog 0.1")
    parser.add_option("-d", "--database",
                      action="store",
                      dest="dbname",
                      help="Database where identities table is stored")
    parser.add_option("-u", "--db-user",
                      action="store",
                      dest="dbuser",
                      default="root",
                      help="Database user")
    parser.add_option("-p", "--db-password",
                      action="store",
                      dest="dbpassword",
                      default="",
                      help="Database password")
    parser.add_option("-g", "--debug",
                      action="store_true",
                      dest="debug",
                      default=False,
                      help="Debug mode")
    parser.add_option("--destroy",
                      action="store_true",
                      dest="destroy",
                      default=False,
                      help="Destroy existing identifiers")


    (opts, args) = parser.parse_args()
    # print(opts)
    if len(args) != 0:
        parser.error("Wrong number of arguments")

    if not(opts.dbname and opts.dbuser):
        parser.error("--database is needed")
        sys.exit(1)
    return opts


def update_uuid_identifier(cursor, uuid, identifier):
    identifier = identifier.replace("'","\\'")
    q = "UPDATE uidentities SET identifier='%s' WHERE uuid='%s'" % (identifier, uuid)
    logging.info(q)
    cursor.execute(q)

def select_identifier(identifiers):
    # Try to select a name, if not a usermail if not an email
    # identifiers = {"names":[],"usernames":[],"emails":[]}
    identifier = None
    # The order in which fields are checked
    fields = ['names','usernames','emails']
    for f in fields:
        if identifier is not None: break
        for iden in identifiers[f]:
            if iden is not None:
                identifier = iden
                if f == 'emails':
                    identifier = identifier.split("@")[0]
                break
    return identifier

def get_uuid_identifier(cursor, uuid):
    identifier = None
    query = "SELECT name, username, email from identities WHERE uuid='%s'"  % (uuid)
    results = cursor.execute(query)

    if results == 0:
        logging.error("Can't find %s identifiers" % (uuid))
    else:
        identifiers = {"names":[],"usernames":[],"emails":[]}
        for identity in cursor.fetchall():
            identifiers['names'].append(identity[0])
            identifiers['usernames'].append(identity[1])
            identifiers['emails'].append(identity[2])
        identifier = select_identifier(identifiers)
    logging.info("%s identifier %s" % (uuid, identifier))
    return identifier

def check_uidentities_table(cursor, con):
    # Add identifier columns if it does not exists
    try:
        query = "SELECT identifier from uidentities LIMIT 1"
        cursor.execute(query)
        logging.info("identifier already exists in uidentities")
    except Exception:
        logging.info("identifier not exists in uidentites. Adding it.")
        q = "ALTER TABLE uidentities ADD identifier VARCHAR(256)"
        cursor.execute(q)
        con.commit()
    return

if __name__ == '__main__':
    opts = None
    opts = read_options()

    if opts.debug:
        logging.basicConfig(level=logging.INFO,format='%(asctime)s %(message)s')
    else:
        logging.basicConfig(level=logging.ERROR,format='%(asctime)s %(message)s')

    if opts.destroy:
        username = raw_input('All current identifiers will be lost. Are you sure? (y/N) ')
        if username != 'y':
            sys.exit(0)

    con = open_database(opts.dbuser, opts.dbpassword, opts.dbname)
    cursor = con.cursor()
    check_uidentities_table(cursor, con)
    q = "SELECT uuid FROM uidentities "
    if not opts.destroy:
        q += "WHERE identifier is NULL"
    # q += " LIMIT 1000"
    res = cursor.execute(q)

    updated = 0
    not_found = 0
    for uuid_row in cursor.fetchall():
        uuid = uuid_row[0]
        identifier = get_uuid_identifier(cursor, uuid)
        if identifier is not None:
            update_uuid_identifier(cursor, uuid, identifier)
            updated += 1
        else:
            logging.info("Can't find identifier for %s" % uuid)
            updated += 1
    con.commit()
    close_database(con)
    
    print("Total identities updated: %i " % (updated))
    print("Total identities not found: %i " % (not_found))
