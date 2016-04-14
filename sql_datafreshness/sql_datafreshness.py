#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 Bitergia
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
# Authors:
#    Luis Cañas-Díaz <lcanas@bitergia.com>

import os
import sys
import time
import ConfigParser
import logging
import MySQLdb
import datetime
import smtplib
import ConfigParser
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from argparse import ArgumentParser

QUERIES = {
    "db_cvsanaly": "SELECT MAX(date) FROM scmlog;",
    "db_gerrit": "SELECT MAX(submitted_on) FROM issues;",
    "db_mlstats": "SELECT MAX(first_date) FROM messages;",
    "db_bicho": "SELECT MAX(updated) FROM (SELECT changed_on AS updated FROM changes UNION SELECT submitted_on AS updated FROM issues UNION SELECT submitted_on AS updated FROM comments) t;",
    "db_irc": "SELECT MAX(date) FROM irclog;",
    "db_pullpo": "SELECT MAX(updated_at) FROM pull_requests;",
    "db_sibyl": "SELECT MAX(updated) FROM (SELECT submitted_on AS updated FROM answers UNION SELECT last_activity_at FROM questions )t;",
    "db_releases": "SELECT MAX(updated_on) FROM releases;",
    "db_mediawiki": "SELECT MAX(date) FROM wiki_pages_revs;",
    "db_downloads": "SELECT MAX(date) FROM downloads_month;",
    "db_eventizer": "SELECT MAX(updated) FROM events;"
}

def get_args():
    parser = ArgumentParser(usage='Usage: %(prog)s [options]',
                            description='Checks data freshness in SQL databases',
                            version='0.1')
    parser.add_argument('-g','--debug', dest='debug',
                        help='Debug mode, disabled by default',
                        required=False, action='store_true')
    parser.add_argument('--conf', dest='config_file',
                        help='Configuration file',
                        required=False)
    parser.add_argument('-s','--send', dest='send',
                        help='Sends the information to the mail. Disabled by default.',
                        required=False,action='store_true')
    parser.add_argument('-f','--file', dest='file',
                        help='Generates a file with the content of the report.',
                        required=False,action='store_true')
    args = parser.parse_args()

    if len(sys.argv)==1:
        parser.print_help()
        sys.exit(1)

    return args

def get_databases(file_path):
    #dbs = ['db_octopus']
    dbs = ['db_cvsanaly','db_gerrit','db_mlstats','db_bicho','db_irc',
            'db_pullpo','db_sibyl','db_releases','db_mediawiki','db_downloads',
            'db_eventizer']

    Config = ConfigParser.ConfigParser()
    Config.read(file_path)

    project_dbs = {}

    for d in dbs:
        if Config.has_option('generic', d):
            project_dbs[d] = Config.get('generic',d)
    return project_dbs

def check_db_freshness(dbinfo, db_user, db_pass):
    db=MySQLdb.connect(user=db_user,passwd=db_pass,db=dbinfo[1])
    c=db.cursor()

    c.execute(QUERIES[dbinfo[0]])
    updated_on = c.fetchone()[0]

    try:
        delta = datetime.datetime.now() - updated_on
        return delta.days
    except:
        return 9999

def find(pattern, root):
    result = []
    for item in os.listdir(root):
        if os.path.isfile(os.path.join(root, item, pattern)):
            result.append(os.path.join(root, item, pattern))
    return(result)

def send_mail(text, subject, msg_from, msg_to):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = msg_from
    msg['To'] = msg_to

    text = 'The owl detected expired SQL data ..\n\n' + text
    body = MIMEText(text, 'plain')

    msg.attach(body)

    # Send the email via our own SMTP server.
    s = smtplib.SMTP('localhost')
    s.sendmail(msg_from, msg_to, msg.as_string())
    s.quit()

def read_opts_file(file_name):
    Config = ConfigParser.ConfigParser()
    Config.read(file_name)

    thresholds = {}
    for x in Config.items('databases'):
        thresholds[x[0]] = int(x[1])

    opts = {}
    opts['dashboards_root'] = Config.get('config','dashboards_root')
    opts['log_file'] = Config.get('config','log_file')
    opts['db_user'] = Config.get('config','db_user')
    opts['db_pass'] = Config.get('config','db_pass')
    opts['default_threshold'] = int(Config.get('config','default_threshold'))
    try:
        opts['email_from'] = Config.get('config','email_from')
    except:
        opts['email_from'] = ''
    try:
        opts['email_to'] = Config.get('config','email_to')
    except:
        opts['email_to'] = ''
    try:
        opts['file_path'] = Config.get('config','file_path')
    except:
        opts['file_path'] = ''
    

    return opts, thresholds

def produce_report(send, file_report_create, file_report_path, data, general_threshold, adhoc_thresholds, msg_from, msg_to=''):
    body_msg = ""
    for p in data.keys():
        logging.info("env: %s" % p)
        aux_lines = []
        for db in data[p].keys():
            age = data[p][db]['days']
            dbname = data[p][db]['dbname']

            if adhoc_thresholds.has_key(dbname):
                max_age = adhoc_thresholds[dbname]
                logging.info('     %s: %s days (threshold = %s)' % (dbname,
                            str(age), max_age))
                if age > max_age:
                    aux_lines.append(' %s: %s days (threshold = %s)' % (dbname,
                                str(age), max_age))
            else:
                logging.info('     %s: %s days' % (dbname, str(age)))
                if age > general_threshold:
                    aux_lines.append(' %s: %s days' % (dbname, str(age)))

        if len(aux_lines) > 0:
            body_msg = body_msg + "\nenv: " + p + "\n"
            for al in aux_lines:
                body_msg = body_msg + " " + str(al) + "\n"
    #end for
    
    if len(body_msg) > 0:
	if send:
		if len(msg_to) > 0:
			msg_subject = 'SQL Data smells (> ' + str(general_threshold) + ' days)'
			send_mail(body_msg, msg_subject, msg_from, msg_to)
			logging.debug("Mail sent to %s" % (msg_to))
		else:
			logging.debug("We cant send the mail because you didn't specify where.")
	if file_report_create:
		if len(file_report_path) > 0:
			target = open(file_report_path+"/mail_report_datafreshness.log."+time.strftime("%Y%m%d"), 'w')
			target.write(body_msg)
			target.close()
		else:
			logging.debug("We cant create the report because you didn't specify where.")
		
    else:
        logging.debug("No report created")

def main():
    args = get_args()
    conf, thresholds = read_opts_file(args.config_file)
    #print myopts

    if args.debug:
        logging.basicConfig(filename=conf["log_file"],level=logging.DEBUG,
                            format='%(asctime)s %(message)s')
    else:
        logging.basicConfig(filename=conf["log_file"],level=logging.INFO,
                            format='%(asctime)s %(message)s')

    logging.info("---")
    logging.info("The owl is watching its SQL territory ..")
    logging.debug("default_threshold = %s" % (str(conf['default_threshold'])))
    conf_files = find('conf/main.conf', conf['dashboards_root'])

    result = {}

    for c in conf_files:
        result[c] = {}

        mydbs = get_databases(c)
        for m in mydbs.items():
            aux = {}
            aux["dbname"] = m[1]
            aux["days"] = check_db_freshness(m, conf['db_user'], conf['db_pass'])
            result[c][m[0]] = aux
        logging.debug("SQL data gathered for %s" % c)

    produce_report(args.send,args.file,conf['file_path'],result, conf['default_threshold'], thresholds,
                    conf['email_from'], conf['email_to'])


if __name__ == '__main__':
    try:
        main()
    except Exception, e:
        s = "Error: %s\n" % str(e)
        sys.stderr.write(s)
        sys.exit(1)

