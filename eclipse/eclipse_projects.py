#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# This script manage the information about Eclipse projects
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

import json
import logging
from optparse import OptionParser
import os.path
import urllib2
import codecs

from eclipse_projects_lib import (
    show_projects_tree, show_projects_hierarchy, show_repos_scm_list,
    show_repos_its_list, show_repos_mls_list, show_repos_scr_list,
    show_duplicates_list, create_projects_db_info, create_affiliations_identities,
    show_changes, show_projects
)

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
    parser.add_option("--hierarchy",
                      action="store_true",
                      dest="json_hierarchy",
                      default=False,
                      help="Create JSON for the hierarchy")
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

    parser.add_option("--changes",
                      action="store_true",
                      dest="changes",
                      help="Detect changes between automator config and projects data")

    (opts, args) = parser.parse_args()
    if len(args) != 0:
        parser.error("Wrong number of arguments")

    if (opts.projects and not opts.automator_file):
        parser.error("projects option needs automator config file")

    if (opts.affiliations_file and not opts.automator_file):
        parser.error("affiliations option needs automator config file")

    if (opts.changes and not opts.automator_file):
        parser.error("changes option needs automator config file")

    return opts

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
    projects_raw = codecs.open(json_file, 'r', 'utf-8').read()
    projects = json.loads(projects_raw)
    projects = projects['projects']

    if opts.tree:
        show_projects_tree(projects, opts.tree_html, opts.template_html)
    elif opts.json_hierarchy:
        show_projects_hierarchy(projects)
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
    elif opts.changes:
        show_changes(projects, opts.automator_file)
    else:
        show_projects(projects)
