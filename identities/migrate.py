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

import argparse
import sys

import MySQLdb

from sortinghat import api
from sortinghat.db.database import Database
from sortinghat.exceptions import NotFoundError, AlreadyExistsError


def main():
    """Link Sorting Hat unique identities to Metrics Grimoire identities"""

    args = parse_args()

    conn = open_database(args, args.database)
    people_uidentities = retrieve_people_uidentities(conn.cursor())
    people_upeople = retrieve_people_upeople(conn.cursor())
    close_database(conn)

    conn = open_database(args, args.identities)
    enrollments = retrieve_upeople_companies(conn.cursor())
    close_database(conn)

    identities = find_matches(people_uidentities, people_upeople, enrollments)

    db = Database(args.user, args.password, args.sortinghat,
                  args.host, args.port)
    merge_identities(db, identities)
    enroll_identities(db, identities, args.insert_orgs)

def open_database(args, name):
    conn = MySQLdb.Connect(host=args.host,
                           port=int(args.port),
                           user=args.user,
                           passwd=args.password,
                           db=name)
    return conn

def close_database(conn):
    conn.close()

def parse_args():
    """Parse arguments from the command line"""

    parser = argparse.ArgumentParser(description="Migrate identities")

    parser.add_argument('-u', '--user', dest='user', default='root',
                        help="Database user")
    parser.add_argument('-p', '--password', dest='password', default='',
                        help="Database password")
    parser.add_argument('-d', '--database', dest='database', required=True,
                        help="Database name")
    parser.add_argument('-s', '--sortinghat', dest='sortinghat', required=True,
                        help="Sortinghat database")
    parser.add_argument('-i', '--identities', dest='identities', required=True,
                        help="Old identities database")
    parser.add_argument('-o', '--insert-orgs', dest='insert_orgs', action='store_true',
                        help='Insert organizations from old identities database')
    parser.add_argument('--host', dest='host', default='localhost',
                        help="Database hostname")
    parser.add_argument('--port', dest='port', default='3306',
                        help="Database port")
    return parser.parse_args()

def merge_identities(sh_db, identities):
    for to_uuid in identities:
        for from_uuid in identities[to_uuid]['matches']:
            api.merge_unique_identities(sh_db, from_uuid, to_uuid)

def enroll_identities(sh_db, identities, insert_orgs=False):
    for uuid in identities:
        for enrollment in identities[uuid]['enrollments']:
            try:
                if insert_orgs:
                    try:
                        api.add_organization(sh_db, enrollment[0])
                    except AlreadyExistsError:
                        pass

                api.add_enrollment(sh_db, uuid, enrollment[0],
                                   enrollment[1], enrollment[2])
                api.merge_enrollments(sh_db, uuid, enrollment[0])
            except (NotFoundError, ValueError), e:
                msg = "Error: %s - (%s, %s, %s, %s)" % (unicode(e), uuid, enrollment[0],
                                                        enrollment[1], enrollment[2])
                print msg.enconde('UTF-8')
            except AlreadyExistsError, e:
                pass

def retrieve_people_uidentities(cursor):
    """Retrieve people uidentities mapping"""

    query = "SELECT people_id, uuid FROM people_uidentities"
    cursor.execute(query)
    results = cursor.fetchall()

    mapping = {r[0] : r[1] for r in results}

    return mapping

def retrieve_people_upeople(cursor):
    """Retrieve people uidentities mapping"""

    query = "SELECT upeople_id, people_id FROM people_upeople"
    cursor.execute(query)
    results = cursor.fetchall()

    mapping = {}

    for r in results:
        upeople_id = str(r[0])
        people_id = str(r[1])

        if upeople_id not in mapping:
            mapping[upeople_id] = [people_id]
        else:
            mapping[upeople_id].append(people_id)

    return mapping

def retrieve_upeople_companies(cursor):
    """Retrieve upeople companies relationships"""

    query = "SELECT upeople_id, name, init, end FROM upeople_companies, companies "
    query += "WHERE company_id = companies.id"
    cursor.execute(query)
    results = cursor.fetchall()

    enrollments = {}

    for r in results:
        upeople_id = str(r[0])
        company = r[1]
        init_date = r[2]
        end_date = r[3]

        enrollment = (company, init_date, end_date)

        if upeople_id not in enrollments:
            enrollments[upeople_id] = [enrollment]
        else:
            enrollments[upeople_id].append(enrollment)

    return enrollments

def find_matches(m_uuids, m_upeople, enrollments):

    matches = {}

    for upeople_id in m_upeople:
        l = m_upeople[upeople_id]

        people_id = l[0]
        uuid = m_uuids[people_id]

        if uuid not in matches:
            matches[uuid] = {'enrollments' : [],
                             'matches' : []}

        if upeople_id in enrollments:
            matches[uuid]['enrollments'] = enrollments[upeople_id]

        if not len(l) > 1:
            continue

        l = l[1:]

        for p in l:
            uuid_p = m_uuids[p]

            if uuid_p != uuid:
                if uuid_p not in matches[uuid]['matches']:
                    matches[uuid]['matches'].append(uuid_p)

    return matches


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        s = "\n\nReceived Ctrl-C or other break signal. Exiting.\n"
        sys.stdout.write(s)
        sys.exit(0)
    except RuntimeError, e:
        s = "Error: %s\n" % str(e)
        sys.stderr.write(s)
        sys.exit(1)
