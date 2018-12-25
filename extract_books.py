#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract_books.py
A script to extract the list of books valid for participating in the
Wikisource contest.

This script is part of wscontest-votecounter.
(<https://github.com/CristianCantoro/wscontest-votecounter>)

---
usage: extract_books.py [-h] [--config CONFIG_FILE] [-d] [-o BOOKS_FILE] [-v]

Extract the list of books valid for the Wikisource contest.

optional arguments:
  -h, --help            show this help message and exit
  --config CONFIG_FILE  INI file to read configs (default: contest.conf.ini)
  -d, --debug           Enable debug output (implies -v)
  -o BOOKS_FILE         TSV file with the books to be processed (default:
                        books.tsv)
  -v, --verbose         Enable verbose output

---
The MIT License (MIT)

wscontest-votecounter:
Copyright (c) 2017 CristianCantoro <kikkocristian@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

import regex
import csv
import time
import logging
import argparse
import configparser
from datetime import datetime, timedelta
import urllib.parse
import urllib.request
import mwparserfromhell

# Try to use yajl, a faster module for JSON
# import json
try:
    import yajl as json
except ImportError:
    import json

### GLOBALS AND DEFAULTS ###
# Files
OUTPUT_BOOKS_FILE = "books.tsv"
CONFIG_FILE = "contest.conf.ini"

# URLs
WIKISOURCE_API = 'https://{lang}.wikisource.org/w/api.php'
OLDWIKISOURCE_API = 'https://wikisource.org/w/api.php'
COMMONS_API = 'https://commons.wikimedia.org/w/api.php'

OLDWIKISOURCE_PREFIXES = set(['old', 'oldwikisource', 'www', ''])

# params
# numeber of times to retry failing requests
MAX_RETRIES = 10
# time (in seconds) to wait between requests
WAIT_TIME = 0.5
# number of revisions
RVLIMIT = 50
### ###

### logging ###
LOGFORMAT_STDOUT = {logging.DEBUG: '%(funcName)s:%(lineno)s - '
                                   '%(levelname)-8s: %(message)s',
                    logging.INFO: '%(levelname)-8s: %(message)s',
                    logging.WARNING: '%(levelname)-8s: %(message)s',
                    logging.ERROR: '%(levelname)-8s: %(message)s',
                    logging.CRITICAL: '%(levelname)-8s: %(message)s'
                    }

# root logger
rootlogger = logging.getLogger()
lvl_logger = logging.DEBUG
rootlogger.setLevel(lvl_logger)

console = logging.StreamHandler()
console.setLevel(lvl_logger)

formatter = logging.Formatter(LOGFORMAT_STDOUT[lvl_logger])
console.setFormatter(formatter)

rootlogger.addHandler(console)

logger = logging.getLogger('score')
logger.setLevel(lvl_logger)


def get_page_revisions(page, lang):

    page = str(page)

    params = {
        'action': 'query',
        'format': 'json',
        'prop': 'revisions',
        'titles': '{page}'.format(page=page),
        'rvlimit': RVLIMIT,
        'rvprop': 'user|timestamp|content'
    }
    params = urllib.parse.urlencode(params).encode('ascii')
    logger.info("\tRequesting '{page}'".format(page=page))

    retries_counter = 0
    retry_fetch = True
    data = {}

    if lang in OLDWIKISOURCE_PREFIXES:
        wikisource_api = OLDWIKISOURCE_API
    else:
        wikisource_api = WIKISOURCE_API.format(lang=lang)

    while retry_fetch and retries_counter < MAX_RETRIES:
        try:
            f = urllib.request.urlopen(source_api, params)
            data = json.loads(f.read().decode('utf-8'))
            retry_fetch = False
        except:
            time.sleep(WAIT_TIME)
            retries_counter += 1
            retry_fetch = True

    page_id = int([k for k in data['query']['pages'].keys()][0])
    revisions = data['query']['pages'][str(page_id)]['revisions']

    return revisions


def read_config(config_file):
    config = {}
    parser = configparser.ConfigParser()
    parser.read(config_file)

    config['contest'] = dict([(k ,v) for k, v in parser['contest'].items()])

    return config


def main(config):
    output = config['books_file']
    contest_start = datetime.strptime(config['contest']['start_date'],
                                      "%Y-%m-%d %H:%M:%S")
    contest_end = datetime.strptime(config['contest']['end_date'],
                                    "%Y-%m-%d %H:%M:%S")
    lang = config['contest']['language']
    debug = config['debug']
    rules_page = config['contest']['rules_page']
    book_regex = config['contest']['book_regex']

    revisions = get_page_revisions(page=rules_page, lang=lang)

    recent_revisions = list()
    if len(revisions) >= RVLIMIT:
        for rev in revisions:
            rev_time = datetime.strptime(rev['timestamp'],
                                         "%Y-%m-%dT%H:%M:%SZ")

            if rev_time >= contest_start and rev_time <= contest_end:
                recent_revisions.append(rev)
    else:
        recent_revisions = revisions
    del revisions

    book_re = regex.compile(book_regex)

    titles = set()
    for rev in recent_revisions:
        wikicode = mwparserfromhell.parse(rev['*'])
        for match in book_re.findall(str(wikicode)):
            titles.add("{title}.{ext}".format(title=match[0],ext=match[1]))


    with open(output, 'w+') as outfile:
        writer = csv.writer(outfile,
                            delimiter='\t',
                            quotechar='"', 
                            quoting=csv.QUOTE_ALL)
        for title in sorted(titles):
            writer.writerow([title])

    return


if __name__ == '__main__':

    DESCRIPTION = 'Extract the list of books valid for the Wikisource contest.'
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument('--config', default=CONFIG_FILE, metavar='CONFIG_FILE',
        help='INI file to read configs (default: {})'.format(CONFIG_FILE))
    parser.add_argument('-d', '--debug', action='store_true',
        help='Enable debug output (implies -v)')
    parser.add_argument('-o', default=OUTPUT_BOOKS_FILE, metavar='BOOKS_FILE',
        help='TSV file with the books to be processed (default: {})'
             .format(OUTPUT_BOOKS_FILE))
    parser.add_argument('-v', '--verbose', action='store_true',
        help='Enable verbose output')

    args = parser.parse_args()

    config_file = args.config
    config = read_config(config_file)

    config['books_file'] = args.o

    # Verbosity/Debug
    config['verbose'] = args.verbose or args.debug
    config['debug'] = args.debug

    lvl_config_logger = logging.WARNING
    if config['verbose']:
        lvl_config_logger = logging.INFO

    if config['debug']:
        lvl_config_logger = logging.DEBUG

    formatter = logging.Formatter(LOGFORMAT_STDOUT[lvl_config_logger])
    console.setFormatter(formatter)
    rootlogger.setLevel(lvl_config_logger)
    logger.setLevel(lvl_config_logger)

    logger.info("Enable verbose output")
    logger.debug("Enable debug")
    logger.debug(args)
    logger.debug(config)

    from pprint import pprint
    # import ipdb; ipdb.set_trace()    
    main(config)

    logger.info("All done!")
