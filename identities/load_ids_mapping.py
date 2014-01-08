#!/usr/bin/python
# -*- coding: utf-8 -*-

# This script feeds identities, upeople and 
# people_countries or people_companies tables 
# from a text file with emails and countries or companies

# Copyright (C) 2013 Bitergia

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

from optparse import OptionParser
import MySQLdb, sys, random

def read_file(filename):
    fd = open(filename, "r")
    lines = fd.readlines()
    fd.close()
    return lines


def parse_file(filename):
    idmail = []
    lines = read_file(filename)
    for l in lines:
        idmail.append(l.split(":"))
    return idmail

def escape_string (message):
    if "\\" in message:
        message = message.replace("\\", "\\\\")
    if "'" in message:
        message = message.replace("'", "\\'")
    return message


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
    parser.add_option("-f", "--file",
                      action="store",
                      dest="data_file",
                      default="email_country.csv",
                      help="File with data in format \"email:country|company\"")
    parser.add_option("-t", "--test",
                      action="store",
                      dest="test",
                      default=False,
                      help="Generate automatic testing data")
    parser.add_option("-k", "--kind",
                      action="store",
                      dest="identity_type",
                      help="Identity kind: name, username, email")
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
    parser.add_option("-m", "--map",
                      action="store",
                      dest="map",
                      help="countries or companies map")

    (opts, args) = parser.parse_args()
    # print(opts)
    if len(args) != 0:
        parser.error("Wrong number of arguments")

    if not(opts.map and opts.data_file and opts.dbname and opts.dbuser):
        parser.error("--map and --file and --database are needed")
        sys.exit(1)
    if (opts.map != "countries" and opts.map != "companies"):
        print("Wrong map: " + opts.map + ". Only countries and companies supported.")
        sys.exit(1)
    if (opts.test != "true" and (opts.identity_type != "email" and opts.identity_type != "username"
        and opts.identity_type != "name")):
        print("Wrong identity type: " + str(opts.identity_type) +
              ". Only name, username and email supported.")
        sys.exit(1)
    return opts


def insert_identity(cursor, debug, data):
    if debug:
        print("INSERT INTO identities (upeople_id, identity, type)\
        VALUES (%s, '%s', '%s')" % data)
    cursor.execute("INSERT INTO identities (upeople_id, identity, type)\
    VALUES (%s, '%s', '%s')" % data)


def insert_upeople(cursor, debug, identity):
    cursor.execute("SELECT MAX(id) FROM upeople")
    maxid = cursor.fetchone()[0]
    myid = int(maxid) + 1
    if debug:
        print("INSERT INTO upeople (id, identifier) VALUES (%s, '%s')"
              % (myid, identity))
    cursor.execute("INSERT INTO upeople (id, identifier) VALUES (%s, '%s')"
                   % (myid, identity))
    return myid

def insert_upeople_country(cursor, upeople_id, country, debug):    
    country_id = None
    query = "SELECT id FROM countries WHERE name = '%s'" % (country)
    results = cursor.execute(query)

    if results == 0:
        query = "INSERT INTO countries (name) VALUES ('%s')" % (country)
        if debug: print(query)
        cursor.execute(query)
        # country_id = con.insert_id()
        country_id = cursor.lastrowid
        print ("New country added " + country)
    else:
        country_id = cursor.fetchall()[0][0]
    
    try:
        cursor.execute("INSERT INTO upeople_countries (country_id, upeople_id) VALUES (%s, '%s')"
                   % (country_id, upeople_id))
    except:
        print ("Mapping already exists for " + upeople_id + " " + country)

def get_company_id(cursor, company, debug):
    company_id = None
    query = "SELECT id FROM companies WHERE name = '%s'" % (company)
    results = cursor.execute(query)

    if results == 0:
        query = "INSERT INTO companies (name) VALUES ('%s')" % (company)
        if debug: print(query)
        cursor.execute(query)
        # company_id = con.insert_id()
        company_id = cursor.lastrowid
        print ("New company added " + company)
    else:
        company_id = cursor.fetchall()[0][0]

    return company_id

def update_upeople_company(cursor, upeople_id, company, debug):
    company_id = get_company_id(cursor, company, debug)
    try:
        cursor.execute("UPDATE upeople_companies SET company_id='%s' WHERE upeople_id='%s'"
                   % (company_id, upeople_id))
    except:
        print ("Mapping already exists for " + str(upeople_id) + " " + company)   

def insert_upeople_company(cursor, upeople_id, company, debug):    
    company_id = get_company_id(cursor, company, debug)
    query = "INSERT INTO upeople_companies (company_id, upeople_id) VALUES (%s, '%s')" % (company_id, upeople_id)
    if (debug): print query
    cursor.execute(query)

def create_tables(cursor, con, opts):
    if (opts.map == "countries"): create_tables_countries(cursor, con)
    elif (opts.map == "companies"): create_tables_companies(cursor, con)

def create_tables_countries(cursor, con):
#   query = "DROP TABLE IF EXISTS countries"
#   cursor.execute(query)
#   query = "DROP TABLE IF EXISTS upeople_countries"
#   cursor.execute(query)

    query = "CREATE TABLE IF NOT EXISTS countries (" + \
            "id int(11) NOT NULL AUTO_INCREMENT," + \
            "name varchar(255) NOT NULL," + \
            "PRIMARY KEY (id)" + \
            ") ENGINE=MyISAM DEFAULT CHARSET=utf8"

    cursor.execute(query)

    query = "CREATE TABLE IF NOT EXISTS upeople_countries (" + \
            "id int(11) NOT NULL AUTO_INCREMENT," + \
            "upeople_id int(11) NOT NULL," + \
            "country_id int(11) NOT NULL," + \
            "PRIMARY KEY (id)" + \
            ") ENGINE=MyISAM DEFAULT CHARSET=utf8"
    cursor.execute(query)

    try:
        query = "CREATE INDEX upc_up ON upeople_countries (upeople_id);"
        cursor.execute(query)
        query = "CREATE INDEX upc_c ON upeople_countries (country_id);"
        cursor.execute(query)
    except Exception:
        print "Indexes upc_up and upc_c already created"

    con.commit()
    return

def create_tables_companies(cursor, con):
#   query = "DROP TABLE IF EXISTS companies"
#   cursor.execute(query)
#   query = "DROP TABLE IF EXISTS upeople_companies"
#   cursor.execute(query)

    query = "CREATE TABLE IF NOT EXISTS companies (" + \
            "id int(11) NOT NULL AUTO_INCREMENT," + \
            "name varchar(255) NOT NULL," + \
            "PRIMARY KEY (id)" + \
            ") ENGINE=MyISAM DEFAULT CHARSET=utf8"

    cursor.execute(query)

    query = "CREATE TABLE IF NOT EXISTS upeople_companies (" + \
            "id int(11) NOT NULL AUTO_INCREMENT," + \
            "upeople_id int(11) NOT NULL," + \
            "company_id int(11) NOT NULL," + \
            "PRIMARY KEY (id)" + \
            ") ENGINE=MyISAM DEFAULT CHARSET=utf8"
    cursor.execute(query)

    try:
        query = "CREATE INDEX upcom_up ON upeople_companies (upeople_id);"
        cursor.execute(query)
        query = "CREATE INDEX upcom_c ON upeople_companies (company_id);"
        cursor.execute(query)
    except Exception:
        print "Indexes upc_up and upcom_c already created"

    con.commit()
    return

def create_test_data(cursor, opts):
    if (opts.map == "countries"): return create_test_data_countries(cursor, opts)
    elif (opts.map == "companies"): create_test_data_companies(cursor, opts)


def create_test_data_countries(cursor, opts):
    test_countries = ['country1', 'country2', 'country3', 'country4', 'country5']
    cursor.execute("DELETE FROM countries")
    cursor.execute("DELETE FROM upeople_countries")
    cursor.execute("SELECT id FROM upeople")
    identities = cursor.fetchall()

    for identity in identities:
        country = test_countries[random.randint(0, len(test_countries) - 1)]
        insert_upeople_country(cursor, identity[0], country, opts.debug)

def create_test_data_companies(cursor, opts):
    test_companies = ['company1', 'company2', 'company3', 'company4', 'company5']
    cursor.execute("DELETE FROM companies")
    cursor.execute("DELETE FROM upeople_companies")
    cursor.execute("SELECT id FROM upeople")
    identities = cursor.fetchall()

    for identity in identities:
        company = test_companies[random.randint(0, len(test_companies) - 1)]
        insert_upeople_company(cursor, identity[0], company, opts.debug)


if __name__ == '__main__':
    opts = None
    opts = read_options()
    con = open_database(opts.dbuser, opts.dbpassword, opts.dbname)

    cursor = con.cursor()
    create_tables(cursor, con, opts)

    if opts.test:  # helper code to test without real data
        print("Creating test data ...")
        create_test_data(cursor, opts)
        sys.exit(0)      

    ids_file = parse_file(opts.data_file)

    count_new = 0
    count_added = 0
    count_changed = 0
    count_cached = 0
    for i in ids_file:
        identity = i[0]
        identity = identity.replace("'", "\\'")  # avoiding ' errors in MySQL
        if (opts.map == "countries"):
            country = escape_string(i[1].rstrip('\n'))
        elif (opts.map == "companies"):
            company = escape_string(i[1].rstrip('\n'))

        q = "SELECT upeople_id, type, identity FROM identities "
        q += "WHERE identity = '%s'" % (identity)
        nmatches = cursor.execute(q)

        if nmatches == 0:
            if opts.debug:
                print("++ %s to be inserted. New upeople tuple to be created"
                      % (str(i)))
            upeople_id = insert_upeople(cursor, opts.debug, identity)
            insert_identity(cursor, opts.debug, (upeople_id, identity, opts.identity_type))
            if (opts.map == "countries"):
                insert_upeople_country(cursor, upeople_id, country, opts.debug)
            elif (opts.map == "companies"):
                insert_upeople_company(cursor, upeople_id, company, opts.debug)
            count_new += 1
        else:
            # there is one or more matches. There could be a lot of them!
            # if there are duplicated upeople_id we use the first we see
            identities = cursor.fetchall()
            upeople_id = identities[0][0]

            if (opts.map == "countries"):
                query = "SELECT upeople_id from upeople_countries \
                         WHERE upeople_id = '%s'" % (upeople_id)

            if (opts.map == "companies"):
                query = "SELECT upeople_id from upeople_companies \
                         WHERE upeople_id = '%s'" % (upeople_id)

            nmatches = cursor.execute(query)

            if nmatches == 0:
                if (opts.map == "countries"):
                    insert_upeople_country(cursor, upeople_id, country, opts.debug)
                elif (opts.map == "companies"):
                    insert_upeople_company(cursor, upeople_id, company, opts.debug)
                count_added += 1
            else:
                if (opts.map == "companies"):
                    update_upeople_company(cursor, upeople_id, company, opts.debug)
                    count_changed += 1
                count_cached += 1
        con.commit()

    close_database(con)
    print("New upeople entries: %s" % (count_new))
    print("Added new country/company to identity:  %s" % (count_added))
    print("Changed country/company to identity:  %s" % (count_changed))
    print("Already stored identities with country/company: %s" % (count_cached))
