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

import re


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
            """ % (title, title, ptl, url, mission)
    cursor.execute(query)

     
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


def insert_project_info(title, repositories, cursor, dbgerrit, dbbicho):
    # This function inserts a new project in table projects and 
    # its associated repositories in table project_repositories.

    # Populating projects table
    project_id = insert_project(cursor, title)

    # Populating projects_children table
    for repo in repositories:
        repo_urls = linked_repos(repo, cursor, dbgerrit, dbbicho)
        for repository in repo_urls:
            data_source = repository
            if repo_urls[repository] <> []:
                url = repo_urls[repository]
                url = "'"+url+"'"
            else:
                continue #this insert shouldn't happen
            query = """
                    insert into project_repositories(project_id, data_source, repository_name)
                    values(%s, '%s', %s)
                    """ % (project_id, data_source, url)
            cursor.execute(query)


def divide_programs(programs):
    # There are 2 main sets of programs:
    # - OpenStack Software that contains all programs with repos using the 
    #   integrated or incubated flag
    # - Rest of the programs, all grouped as in the yaml file. Their repos
    #   do not use the integrated or incubated flag at any time.
    # This function returns a dictionary of 2 keys: 
    # * OpenStack Software
    # * Others
    # Values are represented by a list of programs name (as specified in the yaml file)

    openstack_programs = {}
    openstack_programs["OpenStack Software"] = []
    openstack_programs["Others"] = []

    for program in programs.keys():
        projects = programs[program]["projects"]
        is_openstack_sw = False
        for project in projects:
            # list of projects
            if project.has_key("integrated-since"):
                is_openstack_sw = True
            elif project.has_key("incubated-since"):
                is_openstack_sw = True
        if is_openstack_sw:
            # This program is part of the OpenStack Software list
            openstack_programs["OpenStack Software"].append(program)
        else:
            # This program is part of the Others list
            openstack_programs["Others"].append(program)
        
    return openstack_programs

def insert_relationship(project, subproject, cursor):
    # This function populates the project_children table
    query = """
            select project_id from projects where title='%s'
            """ % (project)
    result = execute_query(cursor, query)
    project_id = result["project_id"]

    query = """
            select project_id from projects where title='%s'
            """ % (subproject)
    result = execute_query(cursor, query)
    subproject_id = result["project_id"]

    query = """
            insert into project_children(project_id, subproject_id)
            values (%s, %s)
            """ % (project_id, subproject_id)
    cursor.execute(query)


def insert_openstack_sw_programs(openstack_sw_list, programs, cursor, dbgerrit, dbbicho):
    # This function insert the OpenStack Software programs
    # dividing their repos into integrated, incubated, clients and others
    integrated = []
    incubated = []
    clients = []
    others = []

    for program in openstack_sw_list:
        projects = programs[program]["projects"]
        for project in projects:
            if project.has_key("incubated-since") and \
               not project.has_key("integrated-since"):
                # This project is still incubated.
                incubated.append(project["repo"])

            if (project.has_key("incubated-since") and \
               project.has_key("integrated-since")) or \
               (project.has_key("integrated-since") and \
               not project.has_key("incubated-since")):
                # This project has been integrated at some point
                integrated.append(project["repo"])

            if not project.has_key("incubated-since") and \
               not project.has_key("integrated-since"):
               # This project may be specs (to be ignored)
               # or a client, having the "client" key string in the name
               # or "others", which is the rest of them.

               if re.match(".*client.*", project["repo"]):
                   clients.append(project["repo"])
               elif re.match(".*specs.*", project["repo"]):
                   continue
               else:
                   others.append(project["repo"])

    # integrated, incubated, clients and others are proper projects in the
    # projects table.
    insert_project_info("OpenStack Software", [], cursor, dbgerrit, dbbicho)
    insert_project_info("integrated", [], cursor, dbgerrit, dbbicho)
    insert_project_info("incubated", incubated, cursor, dbgerrit, dbbicho)
    insert_project_info("clients", clients, cursor, dbgerrit, dbbicho)
    insert_project_info("others", others, cursor, dbgerrit, dbbicho)

    # Adding the relationship between OpenStack Software program and
    # integrated, incubated, clients and others projects.
    insert_relationship("OpenStack Software", "integrated", cursor)
    insert_relationship("OpenStack Software", "incubated", cursor)
    insert_relationship("OpenStack Software", "clients", cursor)
    insert_relationship("OpenStack Software", "others", cursor)

    # And finally, integrated projects are projects by themselves
    for integrated_project in integrated:
        insert_project_info(integrated_project, [integrated_project], cursor, dbgerrit, dbbicho)
        insert_relationship("integrated", integrated_project, cursor)
        

def insert_project(cursor, title):
    # This function returns the associated project_id 
    query = """
            insert into projects (id, title)
            values ('%s', '%s')
            """ % (title, title)
    cursor.execute(query)

    query = """
            select project_id from projects where title='%s'
            """ % (title)
    result = execute_query(cursor, query)
    project_id = result["project_id"]

    return project_id

def insert_other_programs(others, programs, cursor, dbgerrit, dbbicho):
    # All prepositories under each of these programs (others list)
    # are added.
    # So there's a new project with no subproject and a list
    # of repositories.

    for program in others:
        # Populating projects table
        program_id = insert_project(cursor, program)
        projects = programs[program]["projects"]
        for project in projects:
            repo = project["repo"]
            repo_urls = linked_repos(repo, cursor, dbgerrit, dbbicho)

            for repository in repo_urls:
                data_source = repository
                if repo_urls[repository] <> []:
                    url = repo_urls[repository]
                    url = "'"+url+"'"
                else:
                    continue #this insert shouldn't happen
                query = """
                        insert into project_repositories(project_id, data_source, repository_name)
                        values(%s, '%s', %s)
                        """ % (program_id, data_source, url)
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
    
    # There are 2 main sets of programs:
    # - OpenStack Software that contains all programs with repos using the 
    #   integrated or incubated flag
    # - Rest of the programs, all grouped as in the yaml file. Their repos
    #   do not use the integrated or incubated flag at any time.
    openstack_sw_programs = divide_programs(programs)

    # Insert OpenStack Software programs
    insert_openstack_sw_programs(openstack_sw_programs["OpenStack Software"],
                                 programs, db_cursor, opts.dbgerrit, opts.dbbicho)

    # Insert Others programs
    insert_other_programs(openstack_sw_programs["Others"],
                           programs, db_cursor, opts.dbgerrit, opts.dbbicho)

