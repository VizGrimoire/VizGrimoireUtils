#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Bitergia
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
#     Santiago Dueñas <sduenas@bitergia.com>
#

import argparse
import dateutil.parser
import os
import re

from contextlib import contextmanager

from sqlalchemy import create_engine, Column, DateTime, Integer, String
from sqlalchemy.engine.url import URL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool


APACHE_REGEX = re.compile(r'^([(\d\.)]+) - - \[(.+)] "(.+)" 200 .+ "\-" "(.+)"')

package_regexs = [(r'.*\/download.*\/(.*-.*\.t\S+)', 'source'),
                  (r'.*\/(.*_.*_.*\.deb)', 'debian'),
                  (r'.*\/(.*-*-.*\.rpm)', 'rpm')]


# Database

Base = declarative_base()


class DownloadEntry(Base):
    __tablename__ = 'downloads'

    id = Column(Integer, primary_key=True)
    date = Column(DateTime)
    ip = Column(String(39))
    package = Column(String(256))
    protocol = Column(String(256))

    __table_args__ = ({'mysql_charset': 'utf8'})


class Database(object):

    def __init__(self, user, password, database, host='localhost', port='3306'):
        # Create an engine
        self.url = URL('mysql', user, password, host, port, database,
                       query={'charset' : 'utf8'})
        self._engine = create_engine(self.url, poolclass=NullPool, echo=False)
        self._Session = sessionmaker(bind=self._engine)

        # Create the schema on the database.
        # It won't replace any existing schema
        Base.metadata.create_all(self._engine)

    @contextmanager
    def connect(self):
        session = self._Session()

        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

    def clear(self):
        session = self._Session()

        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
            session.commit()
        session.close()


# Apache log parser

def parse_downloads_from_log(filepath):
    downloads = []

    for line in open(filepath, 'rt'):
        entry = line.rstrip('\r\n')

        m = APACHE_REGEX.match(entry)

        if not m:
            continue

        ip = m.group(1)
        dt = dateutil.parser.parse(m.group(2), fuzzy=True)
        protocol = 'HTTP'
        request = m.group(3)

        for regex, tpkg in package_regexs:
            m = re.match(regex, request)

            if m:
                package = m.group(1)
                pkg_type = tpkg
                downloads.append((dt, ip, package, protocol))
                break

    return downloads


def insert_downloads(db, downloads):
    with db.connect() as session:
        for d in downloads:
            entry = DownloadEntry()
            entry.date = d[0]
            entry.ip = d[1]
            entry.package = d[2]
            entry.protocol = d[3]

            session.add(entry)


def get_last_entry(db):
    from sqlalchemy.sql.expression import func

    with db.connect() as session:
        dt = session.query(func.max(DownloadEntry.date)).one()[0]

    if not dt:
        dt = dateutil.parser.parse("1900-01-01")
    return dt

# Argument parser

def parse_args():
    parser = argparse.ArgumentParser()

    # Options
    group = parser.add_argument_group('General options')
    group.add_argument('-u', '--user', dest='user', default='root',
                       help='Database user')
    group.add_argument('-p', '--password', dest='password', default='',
                       help='Database password')
    group.add_argument('-d', '--database', dest='database',
                       help='Database name')
    group.add_argument('--host', dest='host', default='localhost',
                       help='Database host')
    group.add_argument('--port', dest='port', default='3306',
                       help='Database host port')
    group.add_argument('--clear', action='store_true',
                       help='Delete database contents')

    parser.add_argument('logdir', help='Directory where Apache logs are stored')

    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()

    db = Database(args.user, args.password, args.database,
                  args.host, args.port)

    if args.clear:
        db.clear()

    files = os.listdir(args.logdir)
    files.sort()

    max_date = get_last_entry(db).date()

    for logfile in files:
        file_date = dateutil.parser.parse(logfile, fuzzy=True).date()

        if file_date < max_date:
            continue

        filepath = os.path.join(args.logdir, logfile)

        print "Analyzing %s" % logfile

        downloads = parse_downloads_from_log(filepath)
        insert_downloads(db, downloads)
    print "Done"
