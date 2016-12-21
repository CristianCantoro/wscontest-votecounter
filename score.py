#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
score.py
A script to count proofread and validated pages for the Wikisource anniversary
contest.

This script is part of wscontest-votecounter.
(<https://github.com/CristianCantoro/wscontest-votecounter>)

---
usage:
    score.py [-dv] [--booklist-cache BOOKLIST_CACHE] [--cache CACHE_FILE]
             [--config CONFIG_FILE] [--enable-cache] [-f BOOKS_FILE]
             [-o OUTPUT_TSV]
    score.py ( -h | --help )

Count proofread and validated pages for the Wikisource contest.

Optionals:
  -h, --help            show this help message and exit
  --booklist-cache BOOKLIST_CACHE
                        JSON file to read and store the booklist cache
                        (default: {BOOKS_FILE}.booklist_cache.json)
  --cache CACHE_FILE    JSON file to read and store the cache (default:
                        {BOOKS_FILE}.cache.json)
  --config CONFIG_FILE  INI file to read configs (default: contest.conf.ini)
  -d --debug            Enable debug output (implies -v)
  --enable-cache        Enable caching
  -f BOOKS_FILE         TSV file with the books to be processed (default:
                        books.tsv)
  -o OUTPUT_TSV         Output file (default: {BOOKS_FILE}.results.tsv)
  -v --verbose          Enable verbose output

---
The MIT License (MIT)

Original script:
Copyright (c) 2013 Joan Creus <joan.creus.c@gmail.com>

Modified script:
Copyright (c) 2015 Ricordisamoa

wscontest-votecounter:
Copyright (c) 2015 CristianCantoro <kikkocristian@gmail.com>

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

import os
import re
import csv
import time
import codecs
import logging
import argparse
import configparser
from collections import defaultdict
from collections import Counter
from functools import reduce
from operator import add
from datetime import datetime
import urllib.parse
import urllib.request

# Try to use yajl, a faster module for JSON
# import json
try:
    import yajl as json
except ImportError:
    import json

### GLOBALS AND DEFAULTS ###
# Files
BOOKS_FILE = "books.tsv"
CACHE_FILE = "{BOOKS_FILE}.cache.json"
BOOKLIST_CACHE_FILE = "{BOOKS_FILE}.booklist_cache.json"
CONFIG_FILE = "contest.conf.ini"
OUTPUT_TSV = '{BOOKS_FILE}.results.tsv'

# URLs
WIKISOURCE_API = 'https://{lang}.wikisource.org/w/api.php'
COMMONS_API = 'https://commons.wikimedia.org/w/api.php'

# params
MAX_RETRIES = 10

#SAL:
SAL = {0: 0, 25: 1, 50: 2, 75: 3, 100: 4}

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
###


def read_cache(cache_file):
    logger.debug("Reading cache: {}".format(cache_file))
    try:
        with codecs.open(cache_file, 'r', 'utf-8') as f:
            cache = json.load(f)

    # If the file is not found  Python 3.4 will raise FileNotFoundError which is
    # a subclass of IOError.
    # See also:
    # http://sebastianraschka.com/Articles/python3_OSError.html
    except IOError:
        cache = dict()

    return cache


def write_cache(cache, cache_file):
    logger.debug("Writing cache: {}".format(cache_file))
    with codecs.open(cache_file, 'w', 'utf-8') as f:
        json.dump(cache, f)


def get_numpages(book):

    params = {
        'action': 'query',
        'format': 'json',
        'prop': 'imageinfo',
        'titles': 'File:{book}'.format(book=book),
        'iilimit': '50',
        'iiprop': 'size'
    }

    params = urllib.parse.urlencode(params).encode('ascii')
    logger.info("\tRequest image info for file 'File:{book}'".format(book=book))

    with urllib.request.urlopen(COMMONS_API, params) as f:
        data = json.loads(f.read().decode('utf-8'))
        numpages = list(data['query']['pages'].values())[0]['imageinfo'][0]['pagecount']

        return int(numpages)


def get_books(books_file, booklist_cache):

    booklist = 'CACHE_BOOKS_LIST'
    cache = read_cache(booklist_cache)

    if booklist not in cache:
        cache[booklist] = dict()

    with codecs.open(books_file, 'r', 'utf-8') as f:
        lines = f.readlines()
        clean_lines = [line.strip().strip('\"') for line in lines
                       if line.strip() and (not line.startswith("#"))]

    for book in clean_lines:
        if book not in cache[booklist]:
            end = get_numpages(book)
            cache[booklist][book] = end

            write_cache(cache, booklist_cache)

    return [(book, end) for book, end in cache[booklist].items()]


def get_page_revisions(book, page, lang, enable_cache, cache_file):

    cache = None
    if enable_cache:
        cache = read_cache(cache_file)

    page = str(page)
    # Request is cached
    if enable_cache and (book in cache) and (page in cache[book]):
        logger.info("Request is cached...")
        return cache[book][page]

    # Request is NOT cached
    if enable_cache and book not in cache:
        cache[book] = dict()

    params = {
        'action': 'query',
        'format': 'json',
        'prop': 'revisions',
        'titles': 'Page:{book}/{page}'.format(book=book, page=page),
        'rvlimit': '50',
        'rvprop': 'user|timestamp|content'
    }
    params = urllib.parse.urlencode(params).encode('ascii')
    logger.info("\tRequest page 'Page:{book}/{page}'".format(book=book, page=page))

    retries_counter = 0
    retry_fetch = True
    while retry_fetch and retries_counter < MAX_RETRIES:
        try:
            f = urllib.request.urlopen(WIKISOURCE_API.format(lang=lang), params)
            data = json.loads(f.read().decode('utf-8'))
            retry_fetch = False
        except:
            time.sleep(0.5)
            retries_counter += 1
            retry_fetch = True

    if enable_cache:
        cache[book][page] = data
        write_cache(cache, cache_file)
        return cache[book][page]
    else:
        return data


def get_score(books_file,
              contest_start,
              contest_end,
              lang,
              booklist_cache,
              enable_cache,
              cache_file,
              debug=False):
    # defaults are 0
    books = get_books(books_file, booklist_cache)
    tot_punts = dict()
    tot_vali = dict()
    tot_revi = dict()
    
    for i, (book, end) in enumerate(books):
        logger.info("Processing book... \"{}\"".format(book))

        if debug:
            try:
                os.makedirs('debug')
            except OSError as exception:
                import errno
                if exception.errno != errno.EEXIST:
                    raise

            csv_fields = ['user', 'existing_user', 'quality', 'old_user',
                          'old_quality', 'timestamp', 'page']
            revisions_csv = '{book}.revisions.csv'.format(book=book)
            revisions_csvfile = open(os.path.join('debug',revisions_csv), 'w')
            writer = csv.DictWriter(revisions_csvfile,
                                    fieldnames=csv_fields,
                                    delimiter='\t',
                                    quoting=csv.QUOTE_MINIMAL)
            writer.writeheader()

        punts = defaultdict(int)
        vali = defaultdict(int)
        revi = defaultdict(int)

        logger.info("Querying the API...")
        for pag in range(1, end + 1):
            query = get_page_revisions(book,
                                       pag,
                                       lang,
                                       enable_cache,
                                       cache_file)
            try:
                revs = list(query['query']['pages'].values())[0]['revisions'][::-1]
            except KeyError:
                continue

            page_userlist = defaultdict(int)
            for rev in revs:
                user = rev['user']
                page_userlist[user]+=1

            old = None
            oldUser = None
            oldTimestamp = None
            existing_user = 'N'

            # we do not need to check if the user that proofreads the page (SAL 75%)
            # and the user that valides the page are the same.
            # This is alreaady checked on Wikisource.
            # proofreaderUser = None

            for rev in revs:
                timestamp = datetime.strptime(rev['timestamp'], '%Y-%m-%dT%H:%M:%SZ')
                user = rev['user']
                txt = rev['*']
                quality_level, newUser = re.findall('<pagequality level="(\d)" user="(.*?)" />', txt)[0]
                quality_level = int(quality_level)
                newUser = user

                if page_userlist[newUser]>1:
                    if timestamp >= contest_start and timestamp < contest_end:
                        existing_user = 'C'
                    else:
                        existing_user = 'D'
                else:
                    if timestamp >= contest_start and timestamp < contest_end:
                        existing_user = 'P'
                    else:
                        existing_user = 'N'

                if timestamp >= contest_start and timestamp < contest_end:
                    logger.debug("Revision(page={page},user={user},"
                                 "quality={quality},old_user={old_user},"
                                 "old_quality={old_quality},"
                                 "timestamp={timestamp})"
                        .format(page=pag,user=newUser, quality=quality_level,
                                old_user=oldUser, old_quality=old,
                                timestamp=timestamp))
                if debug:
                    newUser_padded = "{: <25}".format(newUser or '')
                    oldUser_padded = "{: <25}".format(oldUser or '')
                    old_quality = 0 if old is None else old

                    writer.writerow({'user': newUser_padded,
                                     'existing_user': existing_user,
                                     'quality': quality_level,
                                     'old_user': oldUser_padded,
                                     'old_quality': old_quality,
                                     'timestamp': timestamp,
                                     'page': pag,
                                     })

                # we do not need to check if proofreaderUser and Validetor
                # are the same (see above)
                # if quality_level == SAL[75] and (old is None or old < SAL[75]):
                #     proofreaderUser = newUser

                # if old is None: Page doesn't exist before
                if quality_level == SAL[75] and (old is None or old < SAL[75]) \
                        and timestamp >= contest_start \
                        and timestamp < contest_end:
                    # User b proofreads the page pag
                    if old == SAL[50]:
                        logger.debug("User: {} - Case 1(a)- Proofread the page, SAL 50% -> SAL 75%".format(newUser))
                        punts[newUser] += 3
                        revi[newUser] += 1
                    elif (old is None or old <= SAL[25]):
                        logger.debug("User: {} - Case 1(b)- Proofread the page, SAL 0/25% -> SAL 75%".format(newUser))
                        punts[newUser] += 5
                        revi[newUser] += 1

                if quality_level == SAL[100] and old == SAL[75] \
                        and timestamp >= contest_start \
                        and timestamp < contest_end:

                    # we do not need to check if proofreaderUser and Validetor
                    # are the same (see above)
                    # assert proofreaderUser is not None
                    # if proofreaderUser != newUser:

                    # User b validates page pag
                    logger.debug("User: {} - Case 2 - Validation".format(newUser))
                    punts[newUser] += 1
                    vali[newUser] += 1

                if quality_level == SAL[75] and old == SAL[100] \
                        and timestamp >= contest_start:
                    # SAL100->SAL75, after the contest started
                    if oldTimestamp >= contest_start and oldTimestamp <= contest_end:
                        # the revert happened during the contest
                        if oldUser != newUser:
                            # exclude the case where the same user reverts herself
                            logger.debug("User: {} - Case 3 - Reverted validation".format(newUser))
                            # we do not need to check if proofreaderUser and Validetor
                            # are the same (see above)
                            # proofreaderUser = newUser
                            punts[oldUser] -= 1
                            vali[oldUser] -= 1

                if (quality_level < SAL[75] or quality_level is None) and old == SAL[75] \
                        and timestamp >= contest_start:
                    # SAL75->SAL0/25/50, after the contest started
                    if oldTimestamp >= contest_start and oldTimestamp <= contest_end:
                        # the revert happened during the contest

                        # we do not need to check if proofreaderUser and Validetor
                        # are the same (see above). Unset the proofreader user.
                        # proofreaderUser = None

                        if quality_level == SAL[50]:
                            logger.debug("User: {} - Case 4(a) - Reverted proofread, SAL 75% -> SAL 50%".format(newUser))
                            punts[oldUser] -= 3
                            revi[oldUser] -= 1
                        else:
                            logger.debug("User: {} - Case 4(a) - Reverted proofread, SAL 75% -> SAL 0/25%".format(newUser))
                            punts[oldUser] -= 5
                            revi[oldUser] -= 1

                if (quality_level < SAL[50] or quality_level is None) and old == SAL[50] \
                        and timestamp >= contest_start:
                    if oldTimestamp >= contest_start and oldTimestamp <= contest_end:

                        # we do not need to check if proofreaderUser and Validetor
                        # are the same (see above)
                        # assert proofreaderUser is None

                        logger.debug("User: {} - Case 5 - Reverted SAL 50% -> SAL 0/25%".format(newUser))
                        punts[oldUser] -= 2
                        revi[oldUser] -= 1

                old = quality_level
                oldUser = newUser
                oldTimestamp = timestamp

            logger.debug(punts)
            logger.debug(vali)
            logger.debug(revi)

        if debug:
            revisions_csvfile.close()

        tot_punts = reduce(add, (Counter(punts), Counter(tot_punts)))
        tot_vali = reduce(add, (Counter(vali), Counter(tot_vali)))
        tot_revi = reduce(add, (Counter(revi), Counter(tot_revi)))

        logger.debug(tot_punts)
        logger.debug(tot_vali)
        logger.debug(tot_revi)

    return tot_punts, tot_vali, tot_revi


def get_rows(punts, vali, revi):
    # sorting:
    # results are ordered by:
    # (punts desc, revi desc, vali desc, username asc)
    # to obtain this first first sort by username ascending, then by
    # (punts, revi, vali) descending
    return [(user, punts[user], vali[user], revi[user])
            for user in sorted(sorted(punts.keys()),
                               key=lambda u: (punts[u], revi[u], vali[u]),
                               reverse=True)]


def write_csv(rows, output):
    csv_fields = ['user', 'punts', 'vali', 'revi']
    with open(output, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile,
                                fieldnames=csv_fields,
                                delimiter='\t',
                                quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()

        for row in rows:
            writer.writerow(dict(zip(csv_fields, row)))


def read_config(config_file):
    config = {}
    parser = configparser.ConfigParser()
    parser.read(config_file)

    config['contest'] = dict([(k ,v) for k, v in parser['contest'].items()])
    return config


def main(config):
    books_file = config['books_file']
    contest_start = datetime.strptime(config['contest']['start_date'], "%Y-%m-%d %H:%M:%S")
    contest_end = datetime.strptime(config['contest']['end_date'], "%Y-%m-%d %H:%M:%S")
    lang = config['contest']['language']
    booklist_cache = config['booklist_cache']
    cache_file = config['cache_file']
    enable_cache = config['enable_cache']
    output = config['output']
    debug = config['debug']

    scores = get_score(books_file,
                       contest_start,
                       contest_end,
                       lang,
                       booklist_cache,
                       enable_cache,
                       cache_file,
                       debug)

    rows = get_rows(*scores)

    write_csv(rows, output)


if __name__ == '__main__':

    DESCRIPTION = 'Count proofread and validated pages for the Wikisource contest.'
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument('--booklist-cache', default=BOOKLIST_CACHE_FILE, metavar='BOOKLIST_CACHE',
                        help='JSON file to read and store the booklist cache (default: {})'.format(BOOKLIST_CACHE_FILE))
    parser.add_argument('--cache', default=CACHE_FILE, metavar='CACHE_FILE',
                        help='JSON file to read and store the cache (default: {})'.format(CACHE_FILE))
    parser.add_argument('--config', default=CONFIG_FILE, metavar='CONFIG_FILE',
                        help='INI file to read configs (default: {})'.format(CONFIG_FILE))
    parser.add_argument('-d', '--debug', action='store_true',
                        help='Enable debug output (implies -v)')
    parser.add_argument('--enable-cache', action='store_true',
                        help='Enable caching')
    parser.add_argument('-f', default=BOOKS_FILE, metavar='BOOKS_FILE',
                        help='TSV file with the books to be processed (default: {})'.format(BOOKS_FILE))
    parser.add_argument('-o', default=OUTPUT_TSV, metavar='OUTPUT_TSV',
                        help='Output file (default: {})'.format(OUTPUT_TSV))
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Enable verbose output')

    args = parser.parse_args()

    config_file = args.config
    config = read_config(config_file)

    config['books_file'] = args.f

    # Booklist file
    if "BOOKS_FILE" in args.booklist_cache:
        config['booklist_cache'] = args.booklist_cache.format(
            BOOKS_FILE=config['books_file'])
    else:
        config['booklist_cache'] = args.booklist_cache

    # Cache file
    config['enable_cache'] = args.enable_cache
    if "BOOKS_FILE" in args.cache:
        config['cache_file'] = args.cache.format(
            BOOKS_FILE=config['books_file'])
    else:
        config['cache_file'] = args.cache

    # TSV output
    if "BOOKS_FILE" in args.o:
        config['output'] = args.o.format(
            BOOKS_FILE=config['books_file'])
    else:
        config['output'] = args.o

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

    main(config)

    logger.info("All done!")
