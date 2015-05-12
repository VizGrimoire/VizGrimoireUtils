#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 Bitergia
#
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
#
# Authors:
#   Alvaro del Castillo San Felix <acs@bitergia.com>
#
# import MySQLdb, os, random, string, sys
# import data_source

import json, os, sys, time, traceback, unittest
import logging
from optparse import OptionParser

class IdentitiesTest(unittest.TestCase):

    supported_data_sources = ["scm","its","scr","mls","irc","mediawiki","releases","qaforums"]

    @staticmethod
    def init():
        opts = read_options()
        Report.init(opts.config_file, opts.metrics_path)
        logging.info("Init Data Source")

    @staticmethod
    def close():
        logging.info("End Data Source")

    def test_people_upeople(self):
        db_identities= Report.get_config()['generic']['db_identities']
        dbuser = Report.get_config()['generic']['db_user']
        dbpass = Report.get_config()['generic']['db_password']

        for ds in Report.get_data_sources():
            if ds.get_name() not in IdentitiesTest.supported_data_sources: continue
            ds_dbname = ds.get_db_name()
            dbname = Report.get_config()['generic'][ds_dbname]
            dsquery = ds.get_query_builder()
            dbcon = dsquery(dbuser, dbpass, dbname, db_identities)
            people_table = "people"
            if ds.get_name() == "irc":
                npeople = dbcon.ExecuteQuery("SELECT COUNT(DISTINCT(nick)) as total from irclog")
            elif ds.get_name() == "mediawiki":
                npeople = dbcon.ExecuteQuery("SELECT COUNT(DISTINCT(user)) as total FROM wiki_pages_revs")
            elif ds.get_name() == "releases":
                npeople = dbcon.ExecuteQuery("SELECT COUNT(DISTINCT(username)) as total FROM users")
            else: 
                npeople = dbcon.ExecuteQuery("SELECT COUNT(*) as total from people")
            nupeople = dbcon.ExecuteQuery("SELECT COUNT(*) as total from people_upeople")
            self.assertEqual(npeople, nupeople, "Data source: " + ds.get_name() + " " + str(npeople) + " " + str(nupeople))
        self.assertTrue(True)

    def get_db_identities_con(self):
        db_identities= Report.get_config()['generic']['db_identities']
        dbuser = Report.get_config()['generic']['db_user']
        dbpass = Report.get_config()['generic']['db_password']
        dbconn = None
        for ds in Report.get_data_sources():
            if ds.get_name() != "scm": continue
            dsquery = ds.get_query_builder()
            dbcon = dsquery(dbuser, dbpass, db_identities, db_identities)
        return dbcon



    def test_max_identities(self):
        dbcon = self.get_db_identities_con()
        # Check there are no person with more than max_ids
        max_ids = "15"
        q = """
            select count(id) as total, upeople_id 
            from identities 
            group by upeople_id 
            having total>=%s order by total 
            desc limit 1
        """ % (max_ids)
        res = check_array_values(dbcon.ExecuteQuery(q))
        self.assertEqual(len(res['total']), 0, res)

        # Check there are no more than max_people with max_ids
        max_ids = "10"
        max_people = "20"
        q = """
            select count(id) as total, upeople_id 
            from identities 
            group by upeople_id 
            having total>=%s order by total 
            desc limit %s
        """ % (max_ids, max_people)
        res = dbcon.ExecuteQuery(q)
        self.assertTrue(len(res['total'])<int(max_people), 
                        "More than " +max_people+" person with more than " + max_ids + " identities")

    def test_max_emails(self):
        dbcon = self.get_db_identities_con()
        # Check there are no person with more than max_ids
        max_emails = "10"
        q = """
            select count(distinct(identity)) as total_emails, upeople_id 
            from identities
            WHERE type = 'email'
            group by upeople_id
            having total_emails>=%s 
            order by total_emails 
            desc limit 1
        """ % (max_emails)
        res = check_array_values(dbcon.ExecuteQuery(q))
        self.assertEqual(len(res['total_emails']), 0, res)

def read_options():
    parser = OptionParser(usage="usage: %prog [options]",
                          version="%prog 0.1")
    parser.add_option("-c", "--config-file",
                      action="store",
                      dest="config_file",
                      default = "../../../conf/main.conf",
                      help="Automator config file")

    parser.add_option("-m", "--metrics",
                  action="store",
                  dest="metrics_path",
                  default = "../../GrimoireLib/vizgrimoire/metrics/",
                  help="Path to the metrics modules to be loaded")

    (opts, args) = parser.parse_args()

    if len(args) != 0:
        parser.error("Wrong number of arguments")

    return opts

def init_env():
    tools_dir = os.path.join("..","..")
    grimoire_lib_dir = os.path.join(tools_dir,"GrimoireLib")
    grimoirelib = os.path.join(grimoire_lib_dir,"vizgrimoire")
    metricslib = os.path.join(grimoire_lib_dir,"vizgrimoire","metrics")
    studieslib = os.path.join(grimoire_lib_dir,"vizgrimoire","analysis")
    alchemy = grimoire_lib_dir
    grimoireutils = os.path.join(tools_dir,"GrimoireUtils")
    for dir in [grimoirelib,metricslib,studieslib,alchemy,grimoireutils]:
        sys.path.append(dir)

if __name__ == '__main__':
    logging.basicConfig(level=logging.WARN,format='%(asctime)s %(message)s')

    init_env()

    from GrimoireUtils import read_main_conf, check_array_values
    from report import Report

    opts = read_options()

    automator = read_main_conf(opts.config_file)

    IdentitiesTest.init()
    suite = unittest.TestLoader().loadTestsFromTestCase(IdentitiesTest)
    unittest.TextTestRunner(verbosity=2).run(suite)

    IdentitiesTest.close()
