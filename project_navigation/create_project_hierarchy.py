#!/usr/bin/python
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
#   Alvaro del Castillo San Felix <acs@bitergia.com>
#   Luis Cañas-Díaz <lcanas@bitergia.com>
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
from GrimoireSQL import SetDBChannel
from GrimoireSQL import ExecuteQuery

def read_options():
    parser = OptionParser(usage="usage: %prog [options]",
                          version="%prog 0.1")
    parser.add_option("-a", "--dbcvsanaly",
                      action="store",
                      dest="dbcvsanaly",
                      help="CVSAnalY db where information is stored")
    parser.add_option("-u","--dbuser",
                      action="store",
                      dest="dbuser",
                      default="root",
                      help="Database user")
    parser.add_option("-p","--dbpassword",
                      action="store",
                      dest="dbpassword",
                      default="",
                      help="Database password")

    (opts, args) = parser.parse_args()
    if len(args) != 0:
        parser.error("Wrong number of arguments")

    return opts

def get_projects_title():
    ## get projects id + title
    q = """SELECT project_id as id, id as string_id, title FROM projects;"""
    ## Warning: project_id is numerical while id is a string
    res = ExecuteQuery(q)
    project_info = {}
    length = len(res["id"])
    cont = 0
    while cont < length:
        escaped_id  = res["string_id"][cont].lower().replace(' ','_')
        project_info[res["id"][cont]] = {"string_id":escaped_id,"title":res["title"][cont]}
        cont += 1
    return(project_info)

def get_project_subproject(project_info):
    ## returns a dict with {"project":["subproject_a",..]}

    dict_res = {}

    ## projects of level 0
    q = "SELECT project_id as id FROM projects WHERE "+\
        "project_id NOT IN (SELECT subproject_id from project_children);"    
    res = ExecuteQuery(q)
    p_no_children = res["id"]
    
    for p in p_no_children:
        key = project_info[p]["string_id"]
        title = project_info[p]["title"]
        dict_res[key] = {"parent_project": "root", "title": title}


    q = "SELECT * FROM project_children"
    relationships = ExecuteQuery(q)

    cont = 0
    length = len(relationships['project_id'])
    while cont < length:
        parent_num_id = relationships['project_id'][cont]
        child_num_id = relationships['subproject_id'][cont]
        parent_str_id = project_info[parent_num_id]["string_id"]
        child_str_id = project_info[child_num_id]["string_id"]
        child_title = project_info[child_num_id]["title"]
        dict_res[child_str_id] = {"parent_project":parent_str_id, "title":child_title}
        cont += 1
    #print project_info            
    return dict_res

if __name__ == '__main__':
    opts = read_options()

    # global connection to the db
    _cursor_identities = None

    logging.basicConfig(level=logging.INFO,format='%(asctime)s %(message)s')
    logging.info("Starting creation of project hierarchy file")

    SetDBChannel(opts.dbuser, opts.dbpassword, opts.dbcvsanaly)

    project_info = get_projects_title()

    tree = {}
    tree = get_project_subproject(project_info)
    tree["root"] = {"title": "Community"} # default value
    import json

    fd = open("test.json","w")
    fd.write(json.dumps(tree))
    fd.close()
    

