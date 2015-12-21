#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014-2015 Bitergia
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

import calendar
import datetime
import dateutil.parser
import requests

from argparse import ArgumentParser

from sqlalchemy import Column, Float, DateTime, Integer,\
    String, create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine.url import URL
from sqlalchemy.pool import NullPool


class Database(object):

    def __init__(self, user, password, database, host='localhost', port='3306'):
        # Create an engine
        self.url = URL('mysql', user, password, host, port, database,
                       query={'charset' : 'utf8'})
        self._engine = create_engine(self.url, poolclass=NullPool, echo=False)
        self._Session = sessionmaker(bind=self._engine)

        # Create the schema on the database.
        # It won't replace any existing schema
        try:
            Base.metadata.create_all(self._engine)
        except OperationalError, e:
            raise DatabaseError(error=e.orig[1], code=e.orig[0])

    def connect(self):
        return self._Session()

    def store(self, session, obj):
        try:
            session.add(obj)
            session.commit()
        except:
            session.rollback()
            raise

    def clear(self):
        session = self._Session()

        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
            session.commit()
        session.close()


class DatabaseError(Exception):
    """Database error exception"""

    def __init__(self, error, code):
        super(DatabaseError, self).__init__()
        self.error = error
        self.code = code

    def __str__(self):
        return "%(error)s (err: %(code)s)" % {'error' : self.error,
                                              'code' : self.code}

# Database model

Base = declarative_base()


class VisitsBase(object):
    id = Column(Integer, primary_key=True)
    date = Column(DateTime(timezone=False))
    unique_visitors = Column(Integer)
    visits = Column(Integer)
    visits_converted = Column(Integer)
    avg_time_on_site = Column(Float)
    sum_visits_lenght = Column(Integer)
    actions = Column(Integer)
    max_actions = Column(Integer)
    actions_per_visit = Column(Float)
    bounce = Column(Integer)
    bounce_rate = Column(Float)


class Visits(VisitsBase, Base):
    __tablename__ = 'visits'
    __table_args__ = ({'mysql_charset': 'utf8'})


class VisitsMonth(VisitsBase, Base):
    __tablename__ = 'visits_month'
    __table_args__ = ({'mysql_charset': 'utf8'})


class CountryBase(object):
    id = Column(Integer, primary_key=True)
    date = Column(DateTime(timezone=False))
    country = Column(String(64))
    unique_visitors = Column(Integer)
    visits = Column(Integer)
    visits_converted = Column(Integer)
    actions = Column(Integer)
    max_actions = Column(Integer)
    sum_visits_lenght = Column(Integer)
    bounce = Column(Integer)


class Country(CountryBase, Base):
    __tablename__ = 'countries'
    __table_args__ = ({'mysql_charset': 'utf8'})


class CountryMonth(CountryBase, Base):
    __tablename__ = 'countries_month'
    __table_args__ = ({'mysql_charset': 'utf8'})


class DownloadBase(object):
    id = Column(Integer, primary_key=True)
    date = Column(DateTime(timezone=False))
    label = Column(String(256))
    unique_downloads = Column(Integer)
    downloads = Column(Integer)
    sum_time_spent = Column(Integer)
    entry_nb_visits = Column(Integer)
    entry_nb_actions = Column(Integer)
    entry_sum_visit_length = Column(Integer)
    entry_bounce_count = Column(Integer)
    exit_nb_visits = Column(Integer)
    sum_daily_nb_uniq_visitors = Column(Integer)
    sum_daily_entry_nb_uniq_visitors = Column(Integer)
    sum_daily_exit_nb_uniq_visitors = Column(Integer)
    url = Column(String(256))


class Download(DownloadBase, Base):
    __tablename__ = 'downloads'
    __table_args__ = ({'mysql_charset': 'utf8'})


class DownloadMonth(DownloadBase, Base):
    __tablename__ = 'downloads_month'
    __table_args__ = ({'mysql_charset': 'utf8'})


class PageBase(object):
    id = Column(Integer, primary_key=True)
    date = Column(DateTime(timezone=False))
    page = Column(String(256))
    visits = Column(Integer)
    entry_nb_visits = Column(Integer)
    entry_nb_actions = Column(Integer)
    entry_sum_visit_length = Column(Integer)
    entry_bounce = Column(Integer)
    bounce_rate = Column(Float)
    exit_nb_visits = Column(Integer)
    exit_rate = Column(Float)
    avg_time_on_page = Column(Float)
    avg_time_generation = Column(Float)
    hits = Column(Integer)
    hits_with_time_generation = Column(Integer)
    min_time_generation = Column(Float)
    max_time_generation = Column(Float)
    time_spent = Column(Integer)
    sum_daily_nb_uniq_visitors = Column(Integer)
    sum_daily_entry_nb_uniq_visitors = Column(Integer)
    sum_daily_exit_nb_uniq_visitors = Column(Integer)
    sum_time_spent = Column(Integer)
    url = Column(String(256))
    segment = Column(String(256))

class Page(PageBase, Base):
    __tablename__ = 'pages'
    __table_args__ = ({'mysql_charset': 'utf8'})


class PageMonth(PageBase, Base):
    __tablename__ = 'pages_month'
    __table_args__ = ({'mysql_charset': 'utf8'})


class Piwik(object):

    VISITS = 'VisitsSummary.get'
    COUNTRIES = 'UserCountry.getCountry'
    DOWNLOADS = 'Actions.getDownloads'
    PAGES = 'Actions.getPageUrls'

    PARAMS = {'module' : 'API',
              'format' : 'JSON'}

    def __init__(self, url, token):
        self.url = url
        self.token = token

    def fetch(self, site_id, start_date='today', end_date='today'):
        visits = self.fetch_visits(site_id, start_date, end_date)
        countries = self.fetch_countries(site_id, start_date, end_date)
        downloads = self.fetch_downloads(site_id, start_date, end_date)
        pages = self.fetch_pages(site_id, start_date, end_date)

        return visits, countries, downloads, pages

    def fetch_visits(self, site_id, start_date, end_date):
        # Visits on the given range
        json = self.__fetch_data(site_id, Piwik.VISITS,
                                 'range', start_date, end_date)
        visits = [self.__parse_visits_entry(json, 'range')]

        # Visits per month
        json = self.__fetch_data(site_id, Piwik.VISITS,
                                 'month', start_date, end_date)
        visits_month = [v for v in self.__parse_visits(json, 'month')]

        visits = visits + visits_month

        return visits

    def fetch_countries(self, site_id, start_date, end_date):
        # Countries data on the given range
        json = self.__fetch_data(site_id, Piwik.COUNTRIES,
                                 'range', start_date, end_date)
        countries = self.__parse_countries(json, 'range')

        # Countries per month
        json = self.__fetch_data(site_id, Piwik.COUNTRIES,
                                 'month', start_date, end_date)
        countries = countries + self.__parse_countries(json, 'month')

        return countries

    def fetch_downloads(self, site_id, start_date, end_date):
        # Downloads on the given range
        json = self.__fetch_data(site_id, Piwik.DOWNLOADS,
                                 'range', start_date, end_date)
        downloads = self.__parse_downloads(json, 'range')

        # Donwloads per month
        json = self.__fetch_data(site_id, Piwik.DOWNLOADS,
                                 'month', start_date, end_date)
        downloads = downloads + self.__parse_downloads(json, 'month')

        return downloads

    def fetch_pages(self, site_id, start_date, end_date):
        # Pages data on the given range
        json = self.__fetch_data(site_id, Piwik.PAGES,
                                 'range', start_date, end_date)
        pages = self.__parse_pages(json, 'range')

        # Pages per month
        json = self.__fetch_data(site_id, Piwik.PAGES,
                                 'month', start_date, end_date)
        pages = pages + self.__parse_pages(json, 'month')

        return pages

    def __fetch_data(self, site_id, method, period, start_date, end_date):
        params = dict(Piwik.PARAMS)
        params['token_auth'] = self.token
        params['method'] = method
        params['idSite'] = site_id
        params['period'] = period
        params['date'] = start_date + ',' + end_date

        if method == Piwik.DOWNLOADS:
            params['expanded'] = 1

        r = requests.get(self.url, params=params)
        json = r.json()

        return json

    def __parse_visits(self, json, period):
        entries = []

        for date in json:
            v = json[date]

            if not v:
                continue

            visits = self.__parse_visits_entry(v, period, date)
            entries.append(visits)

        return entries

    def __parse_visits_entry(self, v, period, date=None):
        if period == 'month':
            visits = VisitsMonth()
        else:
            visits = Visits()

        visits.date = self.__parse_date(date, period)
        visits.unique_visitors = v.get('nb_uniq_visitors', None)
        visits.visits = v['nb_visits']
        visits.visits_converted = v['nb_visits_converted']
        visits.avg_time_on_site = float(v['nb_actions_per_visit'])
        visits.sum_visits_lenght = v['sum_visit_length']
        visits.actions = v['nb_actions']
        visits.max_actions = v['max_actions']
        visits.actions_per_visit = float(v['avg_time_on_site'])
        visits.bounce = v['bounce_count']
        visits.bounce_rate = float(v['bounce_rate'].replace('%', ''))

        return visits

    def __parse_countries(self, json, period):
        if isinstance(json, list):
            entries = self.__parse_countries_entries(json, period)
        else:
            entries = []

            for date in json:
                for c in self.__parse_countries_entries(json[date], period, date):
                    entries.append(c)
        return entries

    def __parse_countries_entries(self, countries, period, date=None):
        entries = []

        dt = self.__parse_date(date, period)

        for c in countries:
            if period == 'month':
                country = CountryMonth()
            else:
                country = Country()

            country.date = dt
            country.country = c['label']
            country.unique_visitors = c.get('nb_uniq_visitors', None)
            country.visits = c['nb_visits']
            country.visits_converted = c['nb_visits_converted']
            country.actions = c['nb_actions']
            country.max_actions = c['max_actions']
            country.sum_visits_lenght = c['sum_visit_length']
            country.bounce = c['bounce_count']

            entries.append(country)

        return entries

    def __parse_downloads(self, json, period):
        if isinstance(json, list):
            entries = self.__parse_downloads_entries(json, period)
        else:
            entries = []

            for date in json:
                for d in self.__parse_downloads_entries(json[date], period, date):
                    entries.append(d)
        return entries

    def __parse_downloads_entries(self, downloads, period, date=None):
        entries = []

        dt = self.__parse_date(date, period)

        for download in downloads:
            if not 'subtable' in download:
                continue
            for d in download['subtable']:
                if period == 'month':
                    download = DownloadMonth()
                else:
                    download = Download()

                download.date = dt
                download.label = d['label']
                download.unique_downloads = d['nb_visits']
                download.downloads = d['nb_hits']
                download.sum_time_spent = d['sum_time_spent']
                download.sum_daily_nb_uniq_visitors = d['sum_daily_nb_uniq_visitors']
                download.url = d.get('url', None)
                download.entry_nb_visits = d.get('entry_nb_visits', None)
                download.entry_nb_actions = d.get('entry_nb_actions', None)
                download.entry_sum_visit_length = d.get('entry_sum_visit_length', None)
                download.entry_bounce_count = d.get('entry_bounce_count', None)
                download.exit_nb_visits = d.get('exit_nb_visits', None)
                download.sum_daily_entry_nb_uniq_visitors = d.get('sum_daily_entry_nb_uniq_visitors', None)
                download.sum_daily_exit_nb_uniq_visitors = d.get('sum_daily_exit_nb_uniq_visitors', None)

                entries.append(download)

        return entries

    def __parse_pages(self, json, period):
        if isinstance(json, list):
            entries = self.__parse_pages_entries(json, period)
        else:
            entries = []

            for date in json:
                for c in self.__parse_pages_entries(json[date], period, date):
                    entries.append(c)
        return entries

    def __parse_pages_entries(self, pages, period, date=None):
        entries = []

        dt = self.__parse_date(date, period)

        for p in pages:
            if period == 'month':
                page = PageMonth()
            else:
                page = Page()

            page.date = dt
            page.page = p['label']
            page.visits = p['nb_visits']
            page.bounce_rate = float(p['bounce_rate'].replace('%', ''))
            page.exit_rate = float(p['exit_rate'].replace('%', ''))
            page.avg_time_on_page = p['avg_time_on_page']
            page.hits = p['nb_hits']
            page.sum_time_spent = p['sum_time_spent']
            page.entry_nb_visits = p.get('entry_nb_visits', None)
            page.entry_nb_actions = p.get('entry_nb_actions', None)
            page.entry_sum_visit_length = p.get('entry_sum_visit_length', None)
            page.entry_bounce = p.get('entry_bounce_count', None)
            page.exit_nb_visits = p.get('exit_nb_visits', None)
            page.sum_daily_nb_uniq_visitors = p.get('sum_daily_nb_uniq_visitors', None)
            page.sum_daily_entry_nb_uniq_visitors = p.get('sum_daily_entry_nb_uniq_visitors', None)
            page.sum_daily_exit_nb_uniq_visitors = p.get('sum_daily_exit_nb_uniq_visitors', None)
            page.url = p.get('url', None)
            page.segment = p.get('segment', None)
            page.avg_time_generation = p.get('avg_time_generation', None)
            page.hits_with_time_generation = p.get('hits_with_time_generation', None)
            page.min_time_generation = p.get('min_time_generation', None)
            page.max_time_generation = p.get('max_time_generation', None)
            page.time_spent = p.get('time_spent', None)

            entries.append(page)

        return entries

    def __parse_date(self, raw_date, period):
        if not raw_date:
            return None

        dt = dateutil.parser.parse(raw_date)
        today = datetime.datetime.now()

        if self.__is_today(dt, today, period):
            dt = datetime.datetime(dt.year, dt.month, today.day)
        else:
            lastday = calendar.monthrange(dt.year, dt.month)[1]
            dt = datetime.datetime(dt.year, dt.month, lastday)

        return dt

    def __is_today(self, dt, today, period):
        is_today = dt.year == today.year

        if period != 'year':
            is_today = is_today and dt.month == today.month
        if period != 'year' and period != 'month':
            is_today = is_today and dt.day == today.day

        return is_today


def parse_args():
    parser = ArgumentParser(usage="Usage: '%(prog)s [options] <url> <site_id>")

    # Database options
    group = parser.add_argument_group('Database options')
    group.add_argument('-u', '--user', dest='db_user',
                       help='Database user name',
                       default='root')
    group.add_argument('-p', '--password', dest='db_password',
                       help='Database user password',
                       default='')
    group.add_argument('-d', dest='db_name', required=True,
                       help='Name of the database where data will be stored')
    group.add_argument('--host', dest='db_hostname',
                       help='Name of the host where the database server is running',
                       default='localhost')
    group.add_argument('--port', dest='db_port',
                       help='Port of the host where the database server is running',
                       default='3306')

    # Piwik options
    group = parser.add_argument_group('Piwik options')
    group.add_argument('--start-date', dest='start_date', required=True)
    group.add_argument('--end-date', dest='end_date', default='today')
    group.add_argument('--key', dest='key', required=True,
                       help='Piwik auth key')

    # Positional arguments
    parser.add_argument('url', help='Piwik server URL')
    parser.add_argument('site_id', help='Identifier of the site')

    # Parse arguments
    args = parser.parse_args()

    return args


def main():
    args = parse_args()
    print args
    try:
        db = Database(args.db_user, args.db_password, args.db_name,
                      args.db_hostname, args.db_port)
    except DatabaseError, e:
        raise RuntimeError(str(e))

    piwik = Piwik(args.url, args.key)
    visits, countries, downloads, pages = piwik.fetch(args.site_id,
                                           args.start_date, args.end_date)

    db.clear()
    session = db.connect()

    for visit in visits:
        db.store(session, visit)
    for country in countries:
        db.store(session, country)
    for download in downloads:
        db.store(session, download)
    for page in pages:
        db.store(session, page)


if __name__ == '__main__':
    import sys

    try:
        main()
    except RuntimeError, e:
        s = "Error: %s\n" % str(e)
        sys.stderr.write(s)
        sys.exit(1)
