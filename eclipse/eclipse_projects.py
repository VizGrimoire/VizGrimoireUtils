#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# This script parses IRC logs and stores the extracted data in
# a database
# 
# Copyright (C) 2012-2013 Bitergia
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


import json
import logging
from optparse import OptionParser
import os.path
import sys
import urllib2

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
    (opts, args) = parser.parse_args()
    if len(args) != 0:
        parser.error("Wrong number of arguments")

    return opts

def parseSCMRepos(repos):
    global total_scm

    basic_scm_url = "http://git.eclipse.org/c"

    repos_list = ""
    for repo in repos:
        if repo['url'] is None:
            if repo['path'] is not None:
                if not 'gitroot' in repo['path']:
                    logging.warn("URL is not git: " + repo['path'])
                else:
                    url = basic_scm_url + repo['path'].split('gitroot')[1]
                    logging.warn("URL is None. URL built: " + url)
                    repos_list += url+","
                    total_scm += 1
        else:
            repos_list += repo['url']+","
            total_scm += 1
    return repos_list.strip(",")

def parseRepos(repos):
    repos_list = ""
    for repo in repos:
        repos_list += repo['url']+","
    return repos_list.strip(",")

def parseITSRepos(repos):
    global total_its

    repos_list = ""
    for repo in repos:
        repos_list += repo['query_url']+","
        total_its += 1
    return repos_list.strip(",")


def parseProject(data):
    print("Title: " + data['title'])
    print("ID: "+data['id'][0]['value']) # safe_value other field
    if (len(data['id'])>1):
        logging.info("More than one identifier")
    print("SCM: " + parseSCMRepos(data['source_repo']))
    print("ITS: " + parseITSRepos(data['bugzilla']))
    if not isinstance(data['dev_list'], list):
        if data['dev_list']['url'] is None:
            logging.warn("URL is None for MLS")
        else:
            print("MLS: " + data['dev_list']['url'])
    print("Forums: " + parseRepos(data['forums']))
    print("Wiki: " + parseRepos(data['wiki_url']))
    if (len(data['parent_project'])>1):
        logging.info("More than one parent")
    if (len(data['parent_project'])>0):
        print("Parent: " + data['parent_project'][0]['id'])
    if (len(data['github_repos'])>0):
        print(data['github_repos'])
    print("---")

def showFields(project):
    for key in project:
        print(key)

def showProjectsTree(projects):
    tree = {}
    # First build the roots structure
    for key in projects:
        data = projects[key]
        if (len(data['parent_project']) == 0):
            tree[key] = []
    # Populate roots
    for key in projects:
        data = projects[key]
        # A project onyl has one parent
        if (len(data['parent_project']) == 1):
            parent = data['parent_project'][0]['id']
            if parent in tree:
                tree[parent].append(data['id'][0]['value'])
    print(tree)

def showProjects(projects):
    global total_its, total_scm, total_projects

    for key in projects:
        total_projects += 1
        parseProject(projects[key])

    logging.info("Total projects: " + str(total_projects))
    logging.info("Total scm: " + str(total_scm))
    logging.info("Total its: " + str(total_its))


if __name__ == '__main__':
    opts = read_options()
    metaproject = opts.url.replace("/","_")
    json_file = "./"+metaproject+".json"

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

    total_projects = total_scm = total_its = 0

    if opts.tree:
        showProjectsTree(projects)
    else:
        showProjects(projects)