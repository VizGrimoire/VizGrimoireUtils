#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# This script reads JSON metrics files from GrimoireLib and combine them 
# in new files.
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
import sys

def read_options():
    parser = OptionParser(usage="usage: %prog [options]",
                          version="%prog 0.1")
    parser.add_option("-a", "--all",
                      action="store_true",
                      dest="all",
                      default=True,
                      help="Create a single JSON file joining all JSON metrics file.")
    parser.add_option("-d", "--dir",
                      action="store",
                      dest="json_dir",
                      help="Directory with all the JSON files")

    (opts, args) = parser.parse_args()
    if len(args) != 0:
        parser.error("Wrong number of arguments")

    if (not opts.json_dir):
        parser.error("Directory with json files should be defined.")

    return opts

def create_all_file():
    json_all_file = os.path.join(opts.json_dir,"all.json")
    logging.info("Joining all JSON files in " + json_all_file)

    if not os.path.isdir(opts.json_dir):
        logging.info("Can't access " + opts.json_dir)
        sys.exit(1)

    json_files = os.listdir(opts.json_dir)

    all_json = {}

    for json_file in json_files:
        fname = os.path.join(opts.json_dir,json_file)
        if os.path.isdir(fname):
            logging.warn(fname + " is a directory. Not including.")
            continue
        print(fname)
        f = open(fname, 'r')
        data = f.read()
        all_json[json_file] = json.loads(data)
        f.close()

    f = open(json_all_file,'w')
    json.dump(all_json, f)
    f.close()


if __name__ == '__main__':
    opts = read_options()

    logging.basicConfig(level=logging.INFO,format='%(asctime)s %(message)s')
    logging.info("Reading JSON files from: " + opts.json_dir)

    if opts.all:
        create_all_file()