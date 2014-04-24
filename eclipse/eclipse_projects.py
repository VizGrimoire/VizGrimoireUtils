#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# This script parses IRC logs and stores the extracted data in
# a database
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
#   Alvaro del Castillo San Felix <acs@bitergia.com>
#


from ConfigParser import SafeConfigParser
import MySQLdb

import json
import logging
from optparse import OptionParser
import pprint
import os.path
import sys
import urllib2, urllib

def read_options():
    parser = OptionParser(usage="usage: %prog [options]",
                          version="%prog 0.1")
    parser.add_option("-u", "--url",
                      action="store",
                      dest="url",
                      default="http://projects.eclipse.org/json/projects/all",
                      help="URL with JSON data for projects")
    parser.add_option("-t", "--tree",
                      action="store_true",
                      dest="tree",
                      default=False,
                      help="Show the projects Tree structure")
    parser.add_option("--html",
                      action="store_true",
                      dest="tree_html",
                      default=False,
                      help="Create HTML for the projects Tree structure")
    parser.add_option("--template",
                      action="store",
                      dest="template_html",
                      default=None,
                      help="HTML template file to be used together with --html")
    parser.add_option("-s", "--scm",
                      action="store_true",
                      dest="scm",
                      default=False,
                      help="List with git repos")
    parser.add_option("-i", "--its",
                      action="store_true",
                      dest="its",
                      default=False,
                      help="List with bugzilla (its) repos")
    parser.add_option("-m", "--mls",
                      action="store_true",
                      dest="mls",
                      default=False,
                      help="List with mailman repos")
    parser.add_option("-r", "--scr",
                      action="store_true",
                      dest="scr",
                      default=False,
                      help="List with gerrit repos")
    parser.add_option("-d", "--dups",
                      action="store_true",
                      dest="dups",
                      default=False,
                      help="Report about repos duplicated in projects")
    parser.add_option("-p", "--projects",
                      action="store_true",
                      dest="projects",
                      default=False,
                      help="Generate the databases for projects to repositories\
                            and to children mapping")
    parser.add_option("-a", "--automator",
                      action="store",
                      dest="automator_file",
                      help="Automator config file")

    parser.add_option("--affiliations",
                      action="store",
                      dest="affiliations_file",
                      help="Creates mapping between identities and affiliations")


    (opts, args) = parser.parse_args()
    if len(args) != 0:
        parser.error("Wrong number of arguments")

    if (opts.projects and not opts.automator_file):
        parser.error("projects option needs automator config file")

    if (opts.affiliations_file and not opts.automator_file):
        parser.error("affiliations option needs automator config file")


    return opts

def get_scm_url(repo):
    basic_scm_url = "http://git.eclipse.org/c"
    url = None
    if repo['path'] is not None:
        if not 'gitroot' in repo['path']:
            logging.warn("Discarding. Can't build URL no git: " + repo['path'])
        else:
            url = basic_scm_url + repo['path'].split('gitroot')[1]
            logging.warn("URL is None. URL built: " + url)
            if (url == "http://git.eclipse.org/c"):
                logging.warn("Discarding. URL path empty: " + url)
                url = None
    return url

def get_scm_repos(project):
    repos = project['source_repo']
    repos_list = []
    for repo in repos:
        if repo['url'] is None:
            url = get_scm_url(repo)
            if url is None: continue
            repos_list.append(url.replace("/c/","/gitroot/"))
        else:
            repos_list.append(repo['url'].replace("/c/","/gitroot/"))
    return repos_list

def parse_repos(repos):
    repos_list = []
    for repo in repos:
        repos_list.append(repo['url'])
    return repos_list

def get_its_repos(project):
    repos = project['bugzilla']
    repos_list = []
    for repo in repos:
        repos_list.append(urllib.unquote(repo['query_url']))
    return repos_list

def get_mls_repos(project):
    repos_list = []
    info = project['dev_list']
    if not isinstance(info, list): # if list, no data
        if info['url'] is not None:
            repos_list.append(info['url'])
    return repos_list

def get_irc_repos(project):
    repos_list = []
    # We don't have data about IRC in projects JSON
    return repos_list

def get_scr_repos(project, scr_url):
    repos_list = []
    repos = get_scm_repos(project)

    for repo in repos:
        if "gitroot" in repo:
            gerrit_project = repo.replace("http://git.eclipse.org/gitroot/","")
            gerrit_project = gerrit_project.replace(".git","")
            repos_list.append(scr_url+"_"+gerrit_project)
    return repos_list


def parse_project(data):
    print("Title: " + data['title'])
    print("ID: "+data['id'][0]['value']) # safe_value other field
    if (len(data['id'])>1):
        logging.info("More than one identifier")
    print("SCM: " + ",".join(get_scm_repos(data)))
    print("ITS: " + ",".join(get_its_repos(data)))
    if not isinstance(data['dev_list'], list):
        if data['dev_list']['url'] is None:
            logging.warn("URL is None for MLS")
        else:
            print("MLS: " + data['dev_list']['url'])
    print("Forums: " + ",".join(parse_repos(data['forums'])))
    print("Wiki: " + ",".join(parse_repos(data['wiki_url'])))
    if (len(data['parent_project'])>1):
        logging.info("More than one parent")
    if (len(data['parent_project'])>0):
        print("Parent: " + data['parent_project'][0]['id'])
    if (len(data['github_repos'])>0):
        print(data['github_repos'])
    print("---")

def get_repos_list(projects, data_source):
    repos_all = []
    for project in projects:
        repos = get_repos_list_project(project, projects, data_source)
        repos_all += repos
    return repos_all

def get_repos_list_project(project, projects, data_source, url = None):
    repos = []
    if data_source == "its":
        repos = get_its_repos(projects[project])
    elif data_source == "scm":
        repos = get_scm_repos(projects[project])
    elif data_source == "mls":
        repos = get_mls_repos(projects[project])
    elif data_source == "scr":
        repos = get_scr_repos(projects[project], url)
    elif data_source == "irc":
        repos = get_irc_repos(projects[project])
    return repos


def get_repos_duplicate_list(projects, kind):
    repos_dup = {}
    repos_seen = {}

    for project in projects:
        if kind == "its":
            repos = get_its_repos(projects[project])
        if kind == "scm":
            repos = get_scm_repos(projects[project])
        if kind == "mls":
            repos = get_mls_repos(projects[project])
        for repo in repos:
            if repo in repos_seen:
                if not repo in repos_dup:
                    repos_dup[repo] = []
                    repos_dup[repo].append(repos_seen[repo])
                repos_dup[repo].append(project)
            else: repos_seen[repo] = project
    return repos_dup

def show_fields(project):
    for key in project:
        print(key)

# We build the tree from leaves to roots
def show_projects_tree(projects, html = False, template_file = None):

    tree = ""
    eclipse_projects_url = "https://projects.eclipse.org/projects"

    def compose_n_ws(number):
        output = ""
        for i in range(0,number):
            output += "&nbsp;&nbsp;"
        return output

    def get_title(project_name):
        return projects[project_name]['title']
    
    def find_children(project):
        children =[]
        for key in projects:
            data = projects[key]
            if (len(data['parent_project']) != 0):
                if project == data['parent_project'][0]['id']:
                    children.append(key)
        return children

    def apply_template(tree, template_file):
        fd = open(template_file, 'r')
        content = fd.read()
        fd.close()
        return content.replace("STRING_TO_BE_REPLACED", tree)
    
    def show_tree(project, level, projects_url):
        tree = ""
        children = find_children(project)
        if len(children) == 0: return (0,tree)
        
        if html:
                id_name = project.replace('.','_') + str(level)
                collapse_html_h = '<div id="collapse%s" class="panel-collapse collapse">' % (id_name)
                tree += collapse_html_h
                tree += "<ul>\n"
        level += 1
        for child in children:
            level_str = ""
            collapse_html = ""
            if (html):
                id_name = child.replace('.','_') + str(level)                
                child_url = "<a href='project.html?project=%s'>%s</a>" % (child, get_title(child))

                for i in range(0, level): level_str += " "
                tree += level_str + "<li>%s %s\n" % (compose_n_ws(level),child_url)
            else:
                for i in range(0, level): level_str += "-"
                tree += level_str + " " + child + "\n"
                
            aux = show_tree(child, level, projects_url)
            nchildren = aux[0]
            childs_tree = aux[1]            
            if len(childs_tree) > 0:
                if html:
                    collapse_html = '<a data-toggle="collapse" data-parent="#accordion" href="#collapse%s">&nbsp;&nbsp;<span class="label">%s subprojects</span> </a>' % (id_name, str(nchildren))
                    tree += collapse_html                    
                    tree += childs_tree
            else:
                tree += childs_tree
            if (html): tree += "</li>\n"
        if html: tree +="</ul></div>\n"
        return (len(children), tree)

    # First detect roots, the build children recursively
    level = 0 # initial level
    for key in projects:
        data = projects[key]
        title = data['title']

        if (len(data['parent_project']) == 0):
            collapse_html = ""
            if html:
                project_url = "<a href='project.html?project=%s'>%s</a>" % (key, title)
                tree +="<ul><li>%s\n" % (project_url)
            else:
                tree += key+"\n"
            #end if
            aux = show_tree(key, level, eclipse_projects_url)
            childs_tree = aux[1]
            nchildren = aux[0]
            if ( len(childs_tree) > 0 and html):
                collapse_html = '<a data-toggle="collapse" data-parent="#accordion" href="#collapse%s">&nbsp;&nbsp;<span class="label">%s subprojects</span></a>' % (key+str(level),nchildren)
                tree += collapse_html
            tree += childs_tree
            if html: tree +="</li></ul>\n"

    if (html and template_file):
        print(apply_template(tree, template_file))
    else:
        print tree

def show_projects(projects):
    total_projects = 0

    for key in projects:
        total_projects += 1
        parse_project(projects[key])

    scm_total = len(get_repos_list(projects, "scm"))
    its_total = len(get_repos_list(projects, "its"))
    mls_total = len(get_repos_list(projects, "mls"))
    scm_dup = len(get_repos_duplicate_list(projects, "scm").keys())
    its_dup = len(get_repos_duplicate_list(projects, "its").keys())
    mls_dup = len(get_repos_duplicate_list(projects, "mls").keys())

    logging.info("Total projects: " + str(total_projects))
    # Including all (svn, cvs, git ...)
    logging.info("Total scm: " + str(scm_total) + " (" + str(scm_dup)+ " duplicates)")
    logging.info("Total its: " + str(its_total) + " (" + str(its_dup)+ " duplicates)")
    logging.info("Total mls: " + str(mls_total) + " (" + str(mls_dup)+ " duplicates)")

def show_repos_scm_list(projects):
    rlist = ""
    all_repos = []
    for key in projects:
        repos = get_scm_repos(projects[key])
        all_repos += repos
    unique_repos = list(set(all_repos))
    rlist += "\n".join(unique_repos)+"\n"
    rlist = rlist[:-1]
    for line in rlist.split("\n"):
        target = ""
        if "gitroot" in line:
            target = line.split("/gitroot/")[1]
        elif "svnroot" in line:
            logging.warning("SVN not supported " + line)
            continue
        else:
            logging.warning("SCM URL special " + line)
        print("git clone " + line + " scm/" + target)

def show_repos_its_list(projects):
    rlist = ""
    all_repos = []
    for key in projects:
        repos = get_its_repos(projects[key])
        all_repos += repos
    unique_repos = list(set(all_repos))
    rlist += "'"+"','".join(unique_repos)
    rlist += "'"
    print(rlist)

def show_repos_mls_list(projects):
    rlist = ""
    all_repos = []
    for key in projects:
        repos = get_mls_repos(projects[key])
        all_repos += repos
    unique_repos = list(set(all_repos))
    rlist += "'"+"','".join(unique_repos)
    rlist += "'"
    print(rlist)

def show_repos_scr_list(projects):
    all_repos = []
    for key in projects:
        repos = get_scm_repos(projects[key])
        all_repos += repos
    unique_repos = list(set(all_repos))
    projects = ""

    for repo in unique_repos:
        if "gitroot" in repo:
            gerrit_project = repo.replace("http://git.eclipse.org/gitroot/","")
            gerrit_project = gerrit_project.replace(".git","")
            projects += "\""+(gerrit_project)+"\""+","
    projects = projects[:-1]
    print(projects)

def show_duplicates_list(projects):
    import pprint
    pprint.pprint(get_repos_duplicate_list(projects, "its"))
    pprint.pprint(get_repos_duplicate_list(projects, "scm"))
    pprint.pprint(get_repos_duplicate_list(projects, "mls"))

def create_projects_schema(cursor):
    project_table = """
        CREATE TABLE projects (
            project_id int(11) NOT NULL AUTO_INCREMENT,
            id varchar(255) NOT NULL,
            title varchar(255) NOT NULL,
            PRIMARY KEY (project_id)
        ) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci
    """
    project_repositories_table = """
        CREATE TABLE project_repositories (
            project_id int(11) NOT NULL,
            data_source varchar(32) NOT NULL,
            repository_name varchar(255) NOT NULL,
            UNIQUE (project_id, data_source, repository_name)
        ) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci
    """
    project_children_table = """
        CREATE TABLE project_children (
            project_id int(11) NOT NULL,
            subproject_id int(11) NOT NULL,
            UNIQUE (project_id, subproject_id)
        ) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci
    """

    # The data in tables is created automatically.
    # No worries about dropping tables.
    cursor.execute("DROP TABLE IF EXISTS projects")
    cursor.execute("DROP TABLE IF EXISTS project_repositories")
    cursor.execute("DROP TABLE IF EXISTS project_children")

    cursor.execute(project_table)
    cursor.execute(project_repositories_table)
    cursor.execute(project_children_table)

def get_project_children(project_key, projects):
    """returns and array with the project names of its children"""
    children = []
    for project in projects:
        data = projects[project]
        if (len(data['parent_project']) == 0):
            continue
        else:
            parent = data['parent_project'][0]['id']
            if parent == project_key:
                children.append(project)
                children += get_project_children(project, projects)
    return children

def get_project_repos(project, projects, data_source):
    """get all repositories for a project in a data source"""
    repos = get_repos_list_project(project, projects, data_source)
    return repos

def set_identities_aff(identities, aff, automator_file):
    """Search for upeople_id for identities and link it to aff"""
    linked = False
    # logging.info("linking %s to %s" % (aff, identities))
    identities = [identity.replace("'","\\'") for identity in identities]
    identities = ",".join(["'"+identity+"'" for identity in identities])

    # Search for upeople_id
    cursor = get_db_cursor_identities(automator_file)
    q = "SELECT DISTINCT(upeople_id) from identities where identity IN (%s)" % identities
    res = execute_query(cursor, q)
    if not isinstance(res['upeople_id'], list): res['upeople_id']=[res['upeople_id']]
    if len(res['upeople_id']) == 0:
        # logging.info("Identities not found %s", identities)
        pass
    else:
        for upid in res['upeople_id']:
            q = """
                INSERT into upeople_companies (upeople_id, company_id)
                VALUES ('%s','%s')
            """ % (upid, aff)
            res = cursor.execute(q)
        # logging.info("Server upeople_id found for  %s" % identities)
        linked = True


    return linked


def create_tables_affiliations(cursor):
    # The data in tables is created automatically.
    # No worries about dropping tables.
    cursor.execute("DROP TABLE IF EXISTS companies")
    cursor.execute("DROP TABLE IF EXISTS upeople_companies")

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
            "init datetime NOT NULL default '1900-01-01'," + \
            "end datetime NOT NULL default '2100-01-01'," + \
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
    return

def get_affiliations(committers):
    all_affs = []
    for person in committers:
        pdata = committers[person]
        if not "affiliations" in pdata: continue
        for aff in pdata['affiliations']:
            person_aff = pdata['affiliations'][aff]['name']
            all_affs.append(person_aff)
    all_affs = list(set(all_affs))

    return all_affs

def get_affiliations_db_data(automator_file):
    """Returns affiliations named with ids in db"""
    cursor = get_db_cursor_identities(automator_file)
    res = execute_query(cursor, "SELECT * from companies")
    return res

# From GrimoireSQL
def execute_query (cursor, sql):
    result = {}
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

def get_db_cursor_identities(automator_file):
    """ One global cursor shared in all code """
    global _cursor_identities

    if (_cursor_identities is None):
        parser = get_automator_parser(automator_file)
        user = parser.get('generic','db_user')
        passwd = parser.get('generic','db_password')
        db = parser.get('generic','db_identities')

        db = MySQLdb.connect(user = user, passwd = passwd, db = db)
        _cursor_identities = db.cursor()

    return _cursor_identities


def create_affiliations(committers, automator_file):
    """Insert into the database the list of affiliations"""

    cursor = get_db_cursor_identities(automator_file)

    create_tables_affiliations(cursor)

    all_affs = get_affiliations(committers)

    for aff in all_affs:
        q = "INSERT INTO companies (name) VALUES ('%s')" % aff
        cursor.execute(q)

    logging.info("Total number of affiliations %i", len(all_affs))

def create_affiliations_identities(affiliations_file, automator_file):
    """map identities to affiliations using data from affiliations_file."""

    if not os.path.isfile(affiliations_file):
        logging.error(affiliations_file + " does not exists.")
        return
    affiliations = open(affiliations_file, 'r').read()
    committers = json.loads(affiliations)['committers']

    create_affiliations(committers, automator_file)

    affs_id = get_affiliations_db_data(automator_file)

    npeople = 0
    npeople_aff = 0
    npeople_found = 0
    for person in committers:
        pdata = committers[person]
        npeople += 1
        if not "affiliations" in pdata: continue
        npeople_aff += 1

        # look for this identifiers in grimoire identities table
        person_identifiers = []
        if 'email' in pdata:
            for email in pdata['email']:
                if email <>'':
                    person_identifiers.append(email)
        if pdata['id'] <> '':
            person_identifiers.append(pdata['id'])
        if pdata['primary'] <> '':
            person_identifiers.append(pdata['primary'])
        if pdata['first'] <> '' and  pdata['last'] <> '':
            person_identifiers.append(pdata['first']+" "+pdata['last'])
        person_identifiers = list(set(person_identifiers))

        person_affs = pdata['affiliations']
        for aff in person_affs:
            person_aff = person_affs[aff]['name']
            person_aff_id = affs_id['id'][affs_id['name'].index(person_aff)]
            if set_identities_aff(person_identifiers, person_aff_id, automator_file):
                npeople_found += 1
    logging.info("Total number of people %i", npeople)
    logging.info("Total number of people with affiliations %i", npeople_aff)
    logging.info("Total number of people found in grimoire %i", npeople_found)

def get_automator_parser(automator_file):
    # Read db config
    parser = SafeConfigParser()
    fd = open(automator_file, 'r')
    parser.readfp(fd)
    fd.close()

    return parser

def create_projects_db_info(projects, automator_file):
    """Create and fill tables for projects, project_repos and project_children"""

    # Read db config
    parser = get_automator_parser(automator_file)
    user = parser.get('generic','db_user')
    passwd = parser.get('generic','db_password')
    db = parser.get('generic','db_identities')
    scr_url = parser.get('gerrit','trackers')

    db = MySQLdb.connect(user = user, passwd = passwd, db = db)
    cursor = db.cursor()
    create_projects_schema(cursor)
    logging.info("Projects tables created")

    # First step, load all projects in the table
    projects_db = {}
    for key in projects:
        title = projects[key]['title']
        q = "INSERT INTO projects (title, id) values (%s, %s)"
        cursor.execute(q, (title, key))
        projects_db[key] = db.insert_id()
    logging.info("Projects added")

    # Insert children for all projects
    for project in projects_db:
        children = get_project_children(project, projects)
        for child in children:
            q = "INSERT INTO project_children (project_id, subproject_id) values (%s, %s)"
            project_id = projects_db[project]
            subproject_id = projects_db[child]
            cursor.execute(q, (project_id, subproject_id))
    logging.info("Projects children added")

    def insert_repos(project_id, repos, data_source):
        for repo in repos:
            q = "INSERT INTO project_repositories VALUES (%s, %s, %s)"
            cursor.execute(q, (project_id, data_source, repo))

    # Insert repositories for all projects
    for project in projects_db:
        repos = get_repos_list_project(project, projects, "scm")
        insert_repos(projects_db[project], repos, "scm")
        repos = get_repos_list_project(project, projects, "its")
        insert_repos(projects_db[project], repos, "its")
        repos = get_repos_list_project(project, projects, "mls")
        insert_repos(projects_db[project], repos, "mls")
        repos = get_repos_list_project(project, projects, "scr", scr_url)
        insert_repos(projects_db[project], repos, "scr")
        repos = get_repos_list_project(project, projects, "irc")
        insert_repos(projects_db[project], repos, "irc")

    logging.info("Projects repositories added")

if __name__ == '__main__':
    opts = read_options()
    metaproject = opts.url.replace("/","_")
    json_file = "./"+metaproject+".json"
    # global connection to the db
    _cursor_identities = None

    logging.basicConfig(level=logging.INFO,format='%(asctime)s %(message)s')
    logging.info("Starting Eclipse projects analysis from: " +  opts.url)

    if not os.path.isfile(json_file):
        purl = urllib2.urlopen(opts.url)
        projects_raw = purl.read().strip('\n')
        f = open(json_file,'w')
        f.write(projects_raw)
        f.close()
    projects_raw = open(json_file, 'r').read()
    projects = json.loads(projects_raw)
    projects = projects['projects']

    if opts.tree:
        show_projects_tree(projects, opts.tree_html, opts.template_html)
    elif opts.scm:
        show_repos_scm_list(projects)
    elif opts.its:
        show_repos_its_list(projects)
    elif opts.mls:
        show_repos_mls_list(projects)
    elif opts.scr:
        show_repos_scr_list(projects)
    elif opts.dups:
        show_duplicates_list(projects)
    elif opts.projects:
        create_projects_db_info(projects, opts.automator_file)
    elif opts.affiliations_file is not None:
        create_affiliations_identities(opts.affiliations_file, opts.automator_file)
    else:
        show_projects(projects)
