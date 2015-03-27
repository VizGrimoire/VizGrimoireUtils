#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (C) 2012-2015 Bitergia
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
# domains_analysis.py
#
# This scripts is based on the outcomes of unifypeople.py and sortinghat
# This will provide three tables:
#    domains
#    upeople_domains for unifypeople
#    uidentities_domains for sortinghat


import logging
import MySQLdb
import sys
import re
from optparse import OptionGroup, OptionParser

def create_tables(db, connector, sortinghat = False):
#   query = "DROP TABLE IF EXISTS domains"
#   connector.execute(query)
#   query = "DROP TABLE IF EXISTS upeople_domains"
#   connector.execute(query)

   query = "CREATE TABLE IF NOT EXISTS domains (" + \
           "id int(11) NOT NULL AUTO_INCREMENT," + \
           "name varchar(255) NOT NULL," + \
           "PRIMARY KEY (id)," + \
           "UNIQUE KEY (name)" + \
           ") ENGINE=MyISAM DEFAULT CHARSET=utf8 "

   connector.execute(query)

   try:
       query = "CREATE INDEX domains_names ON domains (name)"
       connector.execute(query)
   except Exception:
       logging.info ("Index domains.name  already created")

   query = "CREATE TABLE IF NOT EXISTS upeople_domains (" + \
           "id int(11) NOT NULL AUTO_INCREMENT," + \
           "upeople_id int(11) NOT NULL," + \
           "domain_id int(11) NOT NULL," + \
           "init datetime," + \
           "end datetime," + \
           "PRIMARY KEY (id)," + \
           "UNIQUE KEY (upeople_id, domain_id, init)" + \
           ") ENGINE=MyISAM DEFAULT CHARSET=utf8"
   if sortinghat:
       query = "CREATE TABLE IF NOT EXISTS uidentities_domains (" + \
               "id int(11) NOT NULL AUTO_INCREMENT," + \
               "uuid varchar(128) NOT NULL," + \
               "domain_id int(11) NOT NULL," + \
               "init datetime," + \
               "end datetime," + \
               "PRIMARY KEY (id)," + \
               "UNIQUE KEY (uuid, domain_id, init)" + \
               ") ENGINE=MyISAM DEFAULT CHARSET=utf8"
   connector.execute(query)

   db.commit()
   return

def connect(cfg):
   user = cfg.db_user
   password = cfg.db_password
   host = cfg.db_hostname
   db = cfg.db_database

   try:
      db = MySQLdb.connect(user = user, passwd = password, db = db)
      return db, db.cursor()
   except:
      logging.error("Database connection error")
      raise


def execute_query(connector, query):
   results = int (connector.execute(query))
   cont = 0
   if results > 0:
      result1 = connector.fetchall()
      return result1
   else:
      return []

def getOptions():
    parser = OptionParser(usage='Usage: %prog [options]', 
                          description='Domains analysis detection using email addresses',
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
    parser.add_option('-s', '--sortinghat', dest='sortinghat',
                      action="store_true", help='Create sortinghat version')

    (ops, args) = parser.parse_args()

    return ops

def insert_domain(connector, name):
    q = "INSERT INTO domains (name) VALUES ('"+name+"')";
    execute_query(connector, q)

def get_domain_id(connector, name):
    domain_id = None
    q = "SELECT id FROM domains WHERE name ='"+name+"'"
    res = execute_query(connector, q)
    if len(res) == 0:
        insert_domain(connector,name)
        domain_id = get_domain_id(connector, name)
    else: domain_id = res[0][0]
    return domain_id

def insert_upeople_domain(connector, upeople_id, domain_id):
    q = "INSERT INTO upeople_domains(upeople_id, domain_id, init, end) " + \
            "VALUES(" + str(upeople_id) + "," + \
            str(domain_id) + "," + \
            "'1900-01-01', '2100-01-01' );"
    try:
        execute_query(connector, q)
    except:
        # logging.info("Already inserted: " +str(upeople_id)+ " in domain "+ str(domain_id) + " in 1900-01-01")
        pass

def insert_uidentity_domain(connector, uuid, domain_id):
    q = "INSERT INTO uidentities_domains(uuid, domain_id, init, end) " + \
            "VALUES('" + str(uuid) + "'," + str(domain_id) + "," + \
            "'1900-01-01', '2100-01-01' );"
    try:
        execute_query(connector, q)
    except:
        # logging.info("Already inserted: " +str(upeople_id)+ " in domain "+ str(domain_id) + " in 1900-01-01")
        pass


def main(db):
   cfg = getOptions()
   db, connector = connect(cfg)
   create_tables(db, connector, cfg.sortinghat)
   query = "select upeople_id, identity from identities where type='email'"
   if (cfg.sortinghat):
       # query = "select uuid, email from identities where email is not NULL and email<>'None'"
       query = "select uuid, email from identities"
   people = execute_query(connector, query)
   rexp = "(.*@)(.*)"

   for person in people:
      if not cfg.sortinghat:
         upeople_id = int(person[0])
      else:
         uuid = person[0]
      email = str(person[1])

      if re.match(rexp, email):
         m = re.match(rexp, email)
         domain = str(m.groups()[1].split('.')[0])
         domain_id = get_domain_id(connector, domain)
      else:
         domain_id = get_domain_id(connector, 'Unknown')

      if not cfg.sortinghat:
         insert_upeople_domain(connector, upeople_id, domain_id)
      else:
         insert_uidentity_domain(connector, uuid, domain_id)

if __name__ == "__main__":main(sys.argv[1])