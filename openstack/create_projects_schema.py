## Copyright (C) 2014 Bitergia
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 3 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
## GNU General Public License for more details. 
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
##
## This file is a part of GrimoireLib
##  (an Python library for the MetricsGrimoire and vizGrimoire systems)
##
##
## Authors:
##   Daniel Izquierdo-Cortazar <dizquierdo@bitergia.com>
##
## This script parsers the yaml file from the OpenStack Foundation and insert
## the resultant schema in a CVSAnalY database. This allows to have specific
## analysis per group of projects.
##

import yaml

import MySQLdb

from optparse import OptionParser


RELEASES = ["austin", "bexar", "cactus", "diablo", "essex",
            "folsom", "grizzly", "havana", "icehouse", "juno"]

def read_options():


    parser = OptionParser(usage="usage: %prog [options]",
                          version="%prog 0.1")
    parser.add_option("-f", "--file",
                      action="store",
                      dest="file_path",
                      help="Yaml file to be parsed")
    parser.add_option("-u", "--db-user",
                      action="store",
                      dest="dbuser",
                      help="Database user")
    parser.add_option("-p", "--db-password",
                      action="store",
                      dest="dbpassword",
                      help="Database password")
    parser.add_option("-c", "--db-cvsanaly",
                      action="store",
                      dest="dbcvsanaly",
                      help="CVSAnalY database name")
    parser.add_option("-g", "--db-gerrit",
                      action="store",
                      dest="dbgerrit",
                      help="Gerrit database name")
    parser.add_option("-b", "--db-bicho",
                      action="store",
                      dest="dbbicho",
                      help="Bicho database name")
    
    (opts, args) = parser.parse_args()
    return opts

#Improved version from Eclipse projects db schema
def create_projects_schema(cursor):
    project_table = """
        CREATE TABLE projects (
            project_id int(11) NOT NULL AUTO_INCREMENT,
            id varchar(255) NOT NULL,
            title varchar(255) NOT NULL,
            ptl varchar(255) NOT NULL,
            mission text,
            url varchar(255) NOT NULL,
            integrated_since varchar(32),
            incubated_since varchar(32),
            PRIMARY KEY (project_id)
        ) ENGINE=MyISAM DEFAULT CHARSET=utf8
    """
    project_repositories_table = """
        CREATE TABLE project_repositories (
            project_id int(11) NOT NULL,
            data_source varchar(32) NOT NULL,
            repository_name varchar(255) NOT NULL,
            UNIQUE (project_id, data_source, repository_name)
        ) ENGINE=MyISAM DEFAULT CHARSET=utf8
    """
    project_children_table = """
        CREATE TABLE project_children (
            project_id int(11) NOT NULL,
            subproject_id int(11) NOT NULL,
            UNIQUE (project_id, subproject_id)
        ) ENGINE=MyISAM DEFAULT CHARSET=utf8
    """

    # The data in tables is created automatically.
    # No worries about dropping tables.
    cursor.execute("DROP TABLE IF EXISTS projects")
    cursor.execute("DROP TABLE IF EXISTS project_repositories")
    cursor.execute("DROP TABLE IF EXISTS project_children")

    cursor.execute(project_table)
    cursor.execute(project_repositories_table)
    cursor.execute(project_children_table)

# From GrimoireSQL
def execute_query (cursor, sql):
    result = {}
    cursor.execute("SET NAMES utf8")
    cursor.execute(sql)
    rows = cursor.rowcount
    columns = cursor.description

    for column in columns:
        result[column[0]] = []
    if rows > 1:
        for value in cursor.fetchall():
            for (index,column) in enumerate(value):
                result[columns[index][0]].append(column)
    elif rows == 1:
        value = cursor.fetchone()
        for i in range (0, len(columns)):
            result[columns[i][0]] = value[i]
    return result

def connect(database, user, password):
   host = 'localhost'
   try:
      db =  MySQLdb.connect(host,user,password,database)
      return db.cursor()
   except:
      print("Database connection error")


def insert_program(program, program_name, cursor):
    # A program consists of:
    # - codename
    # - ptl
    # - url
    # - mission
    # - projects
    title = program_name
    identifier = program_name
    if program.has_key("codename"):
        identifier = program["codename"]
    ptl = program["ptl"]
    url = program["url"]
    mission = ""
    if program.has_key("mission"):
        mission = program["mission"]
    projects = program["projects"]

    # Insert program info
    query = """
            insert into projects (id, title, ptl, url, mission)
            values ('%s', '%s', '%s', '%s', '%s')
            """ % (identifier, title, ptl, url, mission)
    cursor.execute(query)

     
def associated_projects(programs, programs_list):

    releases_programs = {}
    for release in RELEASES:
        # init structure
        releases_programs[release] = []
  
    for program in programs.keys():
        projects = programs[program]["projects"]
        for project in projects:
            # list of projects
            if project.has_key("integrated-since"):
                release = project["integrated-since"]
                program_id = programs_list.index(program) + 1
                releases_programs[release].append(program_id)
    previous = []
    for release in RELEASES:
        releases_programs[release].extend(previous)
        previous = releases_programs[release]

    return releases_programs

                
def insert_releases_programs(releases_programs, programs_list, cursor):
    # insert releases in database
    count = 1 #db id counter
    for release in RELEASES:
        # Insert release as a project of first level
        query = """
                insert into projects(id, title, url, ptl)
                values('%s', '%s', '%s', '%s')
                """ % ("release-"+release, "release-"+release, "", "")
        cursor.execute(query)

        programs = releases_programs[release]
        for program in programs:
            # populate project_children table
            query = """
                    insert into project_children(project_id, subproject_id)
                    values(%s, %s)
                    """ % (len(programs_list) + count, program)
            cursor.execute(query)

        count = count + 1

def linked_repos(repo, cursor, dbgerrit, dbbicho):
    # This function looks for repositories similar to the repos variable
    repositories = {}

    # CVSAnalY db
    query = "select uri from repositories where uri like '%"+repo+"' or uri like '%"+repo+".git'"
    result = execute_query(cursor, query)
    repositories["scm"] = result["uri"]
    
    # Gerrit db
    query = "select url from "+dbgerrit+".trackers where url like '%"+repo+"'"
    result = execute_query(cursor, query)
    repositories["gerrit"] = result["url"]

    # Bicho db
    tracker = repo.split("/")[1]
    query = "select url from "+dbbicho+".trackers where url like '%/"+tracker+"'"
    result = execute_query(cursor, query)
    repositories["its"] = result["url"]
    
    return repositories


def insert_projects_per_program(programs, programs_list, cursor, dbgerrit, dbbicho):
    # For each program, there is a list of projects that
    # is inserted in the project_repositories table.
    # Each project entry may have a repository at least
    # in the scm, gerrit and bicho databases.

    for program in programs:
        projects = programs[program]["projects"]
        for project in projects:
            # this repo contains info structured such as
            # [openstack|openstack-infra]/project
            repo = project["repo"]
            repositories = linked_repos(repo, cursor, dbgerrit, dbbicho)
            for repository in repositories:
                project_id = programs_list.index(program) + 1
                data_source = repository
                if repositories[repository] <> []:
                    url = repositories[repository]
                    url = "'"+url+"'"
                else:
                    continue #this insert shouldn't happen
                query = """
                        insert into project_repositories(project_id, data_source, repository_name)
                        values(%s, '%s', %s)
                        """ % (project_id, data_source, url)
                cursor.execute(query) 
            

if __name__ == '__main__':
    # Parse command line options
    opts = read_options()

    # Init db schema and connector
    db_cursor = connect(opts.dbcvsanaly, opts.dbuser, opts.dbpassword)
    create_projects_schema(db_cursor)

    # Parse yaml file into dictionary
    stream = open(opts.file_path, 'r')
    programs = yaml.load(stream)
    
    # Insert each of the programs information into the
    # db schema
    programs_list = []
    for program_name in programs.keys():
        programs_list.append(program_name)
        insert_program(programs[program_name], program_name, db_cursor)

    releases_programs = {}
    # Each OpenStack release contains a subset
    # of all of the official programs (except typically
    # the last release that contains all of them)
    # Thus, a release is considered as a meta-project that 
    # contains a list of subprojects (that contains repositories)
    releases_programs = associated_projects(programs, programs_list)
    insert_releases_programs(releases_programs, programs_list, db_cursor)

    # And finally, insert projects per program
    insert_projects_per_program(programs, programs_list, db_cursor, opts.dbgerrit, opts.dbbicho)

