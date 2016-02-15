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
import ConfigParser
import logging
import MySQLdb
import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from argparse import ArgumentParser

QUERIES = {
    "db_cvsanaly": "SELECT MAX(date) FROM scmlog;",
    "db_gerrit": "SELECT MAX(submitted_on) FROM issues;",
    "db_mlstats": "SELECT MAX(first_date) FROM messages;",
    "db_bicho": "SELECT MAX(submitted_on) FROM issues;",
    "db_irc": "SELECT MAX(date) FROM irclog;",
    "db_pullpo": "SELECT MAX(updated_at) FROM pull_requests;",
    "db_sibyl": "SELECT MAX(submitted_on) FROM answers;",
    "db_releases": "SELECT MAX(updated_on) FROM releases;",
    "db_mediawiki": "SELECT MAX(date) FROM wiki_pages_revs;",
    "db_downloads": "SELECT MAX(date) FROM downloads_month;",
    "db_eventizer": "SELECT MAX(updated) FROM events;"
}

def get_options():
    parser = ArgumentParser(usage='Usage: %(prog)s [options]',
                            description='Checks data freshness in SQL databases',
                            version='0.1')
    parser.add_argument('-t','--threshold', dest='threshold',
                        help='Show data older than the threshold',
                        required=False, type=int)
    parser.add_argument('-d','--directory', dest='directory',
                        help='Directory where automator environments are deployed',
                        required=True)
    parser.add_argument('-g','--debug', dest='debug',
                        help='Debug mode, disabled by default',
                        required=False, action='store_true')
    parser.add_argument('-l','--logfile', dest='logfile',
                        help='Log file',
                        required=True)
    parser.add_argument('--from', dest='sender',
                        help='Mail sender',
                        required=True)
    parser.add_argument('--to', dest='recipient',
                        help='Mail recipient',
                        required=True)
    parser.add_argument('--db_user', dest='db_user',
                        help='Database user',
                        required=True)
    parser.add_argument('--db_pass', dest='db_pass',
                        help='Database password',
                        required=False, default='')
    args = parser.parse_args()

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

def produce_report(data, threshold, msg_from, msg_to):
    body_msg = ""
    for p in data.keys():
        logging.info("env: %s" % p)
        aux_lines = []
        for db in data[p].keys():
            age = data[p][db]['days']
            dbname = data[p][db]['dbname']
            logging.info('     %s: %s days' % (dbname, str(age)))
            if age > threshold:
                aux_lines.append(' %s: %s days' % (dbname, str(age)))

        if len(aux_lines) > 0:
            body_msg = body_msg + "\nenv: " + p + "\n"
            for al in aux_lines:
                body_msg = body_msg + " " + str(al) + "\n"
    #end for
    if len(body_msg) > 0:
        msg_subject = 'SQL Data smells (> ' + str(threshold) + ' days)'
        send_mail(body_msg, msg_subject, msg_from, msg_to)

def main():
    opts = get_options()
    if opts.debug:
        logging.basicConfig(filename=opts.logfile,level=logging.DEBUG,
                            format='%(asctime)s %(message)s')
    else:
        logging.basicConfig(filename=opts.logfile,level=logging.INFO,
                            format='%(asctime)s %(message)s')

    logging.info("The owl is watching its SQL territory ..")
    logging.debug("threshold = %s" % (str(opts.threshold)))
    conf_files = find('conf/main.conf', opts.directory)

    result = {}

    for c in conf_files:
        result[c] = {}

        mydbs = get_databases(c)
        for m in mydbs.items():
            aux = {}
            aux["dbname"] = m[1]
            aux["days"] = check_db_freshness(m, opts.db_user, opts.db_pass)
            result[c][m[0]] = aux
        logging.debug("data gathered for %s" % c)

    produce_report(result, opts.threshold, opts.sender, opts.recipient)


if __name__ == '__main__':
    try:
        main()
    except Exception, e:
        s = "Error: %s\n" % str(e)
        sys.stderr.write(s)
        sys.exit(1)
