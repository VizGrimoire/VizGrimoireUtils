#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Bitergia
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
#     Alberto Martín <alberto.martin@bitergia.com>
#

import github3
import os, logging
from argparse import ArgumentParser

def get_options():
    parser = ArgumentParser(usage='Usage: %(prog)s [options]', 
                            description='Clone repositories from GitHub',
                            version='0.1')
    parser.add_argument('-u','--user', dest='user',
                        help='Github User name', 
			required=True)
    parser.add_argument('-p', '--password', dest='password',
                        help='Github User password', 
			required=True)
    parser.add_argument('-o','--organization', dest='org',
                        help='Name of the Organization to analyze repositories',
          		required=True)
    parser.add_argument('-t','--type', dest='type_of_source',
		        help='Type of the repository to analyze',
                        default='sources')
    
    args = parser.parse_args()
    
    return args

def login(args):
    user = args.user
    password = args.password
    gh = github3.login(user, password=password)
    return gh

def clone_repos(organization, type_of_source, gh):
    try:
        org = gh.organization(organization)
        repos = org.repositories(type=type_of_source)
        for repo in repos:
            org, repo = str(repo).split("/")
            if os.path.exists(str(repo)) == True:
                print("The repository %s already exists" % repo)
            else:
                print("Cloning repo %s" % str(repo))
                os.system("git clone --quiet " + "https://github.com" + "/" + org + "/" + repo)
    except github3.exceptions.AuthenticationFailed, e:
        raise Exception(str(e))

def main():
    logging.basicConfig(level=logging.INFO,format='%(asctime)s %(message)s')

    args = get_options()
    gh = login(args)
    request = clone_repos(args.org,args.type_of_source, gh)

if __name__ == '__main__':

    import sys

    try:
        main()
    except Exception, e:
	s = "Error: %s\n" % str(e)
        sys.stderr.write(s)
        sys.exit(1) 
