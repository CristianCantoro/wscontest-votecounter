#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
The MIT License (MIT)

Copyright (c) 2013 Joan Creus <joan.creus.c@gmail.com>
Copyright (c) 2015 Ricordisamoa and CristianCantoro <kikkocristian@gmail,com>

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
import re
import csv
import json
import codecs
import logging
import argparse
import configparser
from collections import defaultdict
from collections import Counter
from functools import reduce
from operator import add
from datetime import datetime
from html import escape
import urllib.parse
import urllib.request

### GLOBALS AND DEFAULTS ###
# Files
BOOKS_FILE = "books.tsv"
TEMPLATE_FILE = "index.template.html"
CACHE_FILE = "books_cache.json"
CONFIG_FILE = "contest.conf.ini"
OUTPUT_CSV = 'results.tsv'
OUTPUT_HTML = 'index.html'

# URLs
WIKISOURCE_API = 'https://{lang}.wikisource.org/w/api.php'
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


def get_books(books_file):
    with codecs.open(books_file, 'r', 'utf-8') as f:
        lines = f.readlines()
        lines = [line for line in lines
                 if line.strip() and (not line.startswith("#"))]
        clean_lines = ['\t'.join([el.strip('\"')
                                  for el in line.split('\t') if el])
                       for line in lines]

    for line in clean_lines:
        spl = line.split('\t', 2)
        yield spl[0], int(spl[1])


def get_page_revisions(book, page, lang):
    params = {
        'action': 'query',
        'format': 'json',
        'prop': 'revisions',
        'titles': 'Page:{book}/{page}'.format(book=book, page=page),
        'rvlimit': '50',
        'rvprop': 'user|timestamp|content'
    }
    params = urllib.parse.urlencode(params).encode('ascii')
    logger.info("\tRequest page 'Page:{}/{}'".format(book, page))
    with urllib.request.urlopen(WIKISOURCE_API.format(lang=lang),
                                params) as f:
        return json.loads(f.read().decode('utf-8'))


def read_cache(cache_file):
    logger.debug("Reading cache")
    try:
        with codecs.open(cache_file, 'r', 'utf-8') as f:
            cache = json.load(f)
    except FileNotFoundError:
        cache = dict()

    return cache


def write_cache(cache):
    logger.debug("Writing cache")
    with codecs.open(CACHE_FILE, 'w', 'utf-8') as f:
        json.dump(cache, f)


def get_score(books_file, contest_start, contest_end, lang, cache_file):
    # defaults are 0
    books = get_books(books_file)
    tot_punts = dict()
    tot_vali = dict()
    tot_revi = dict()
    
    for i, (book, end) in enumerate(books):
        logger.info("Processing book... \"{}\"".format(book))

        punts = defaultdict(int)
        vali = defaultdict(int)
        revi = defaultdict(int)

        cache = read_cache(cache_file)

        if book in cache:
            logger.info("Book \"{}\" is cached... (continue)".format(book))
            punts = cache[book]['punts']
            vali = cache[book]['vali']
            revi = cache[book]['revi']
        else:
            logger.info("Querying the API...")
            for pag in range(1, end + 1):
                query = get_page_revisions(book, pag, lang)
                try:
                    revs = list(query['query']['pages'].values())[0]['revisions'][::-1]
                except KeyError:
                    continue
                old = None
                oldUser = None
                oldTimestamp = None
                for rev in revs:
                    timestamp = datetime.strptime(rev['timestamp'], '%Y-%m-%dT%H:%M:%SZ')
                    user = rev['user']
                    txt = rev['*']
                    a, b = re.findall('<pagequality level="(\d)" user="(.*?)" />', txt)[0]
                    a = int(a)
                    b = user
                    if a == 3 and (old is None or old < 3) and timestamp >= contest_start and timestamp < contest_end:
                        # User b proofreads the page pag
                        # if old is None:
                        #     print("Page doesn't exist before.")
                        punts[b] += 2
                        revi[b] += 1
                    if a == 3 and old == 4 and timestamp >= contest_start and timestamp < contest_end:
                        if oldTimestamp >= midterm1 and oldTimestamp < DATE2:
                            punts[oldUser] -= 1
                            vali[oldUser] -= 1
                    if a == 4 and old == 3 and timestamp >= contest_start and timestamp < contest_end:
                        # User b validates page pag
                        punts[b] += 1
                        vali[b] += 1
                    if a < 3 and old == 3 and timestamp >= contest_start and timestamp < contest_end:
                        if oldTimestamp >= contest_start and oldTimestamp < contest_end:
                            punts[oldUser] -= 2
                            revi[oldUser] = vali[oldUser] - 1  # sic?!?
                old = a
                oldUser = b
                oldTimestamp = timestamp

        tot_punts = reduce(add, (Counter(punts), Counter(tot_punts)))
        tot_vali = reduce(add, (Counter(vali), Counter(tot_vali)))
        tot_revi = reduce(add, (Counter(revi), Counter(tot_revi)))

        cache[book] = dict()
        cache[book]['punts'] = punts
        cache[book]['vali'] = vali
        cache[book]['revi'] = revi
        write_cache(cache)

        logger.debug(tot_punts)
        logger.debug(tot_vali)
        logger.debug(tot_revi)

    return tot_punts, tot_vali, tot_revi


def format_user(name, lang):
    user_string = '<a href="//{lang}.wikisource.org/wiki/User:{name}">{name}</a>'
    return user_string.format(lang=lang, name=escape(name))


def get_html_rows(rows, lang):
    table_string = '<tr><td>{0}</td><td>{1}</td><td>{2}</td><td>{3}</td></tr>'
    return [table_string.format(format_user(user, lang),
                                user_punts,
                                user_vali,
                                user_revi)
            for user, user_punts, user_vali, user_revi in rows
            ] 


def get_rows(punts, vali, revi):
    return [(user, punts[user], vali[user], revi[user])
            for user in sorted(punts.keys(),
                               key=lambda u: punts[u],
                               reverse=True)
            ]


def write_html(rows, lang):
    with open(config['html_template'], 'r') as f:
        template = f.read()

    html_rows = get_html_rows(rows, lang=lang)
    content = template.replace("{{{rows}}}", '\n'.join(html_rows))
    with codecs.open('index.html', 'w', 'utf-8') as f:
        f.write(content)


def write_csv(rows):
    csv_fields = ['user', 'punts', 'vali', 'revi']
    with open(OUTPUT_CSV, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile,
                                fieldnames=csv_fields,
                                delimiter='\t',
                                quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()

        import pdb
        pdb.set_trace()

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
    cache_file = config['cache_file']

    scores = get_score(books_file, contest_start, contest_end, lang, cache_file)
    rows = get_rows(*scores)

    write_csv(rows)

    if config['html']:
        write_html(rows, lang)


if __name__ == '__main__':

    DESCRIPTION = 'Count proofread pages for the Wikisource contest.'
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument('--cache', default=CACHE_FILE,
                        metavar='CACHE_FILE',
                        help='JSON file to read and store the cache (default: {})'.format(CACHE_FILE))
    parser.add_argument('--config', default=CONFIG_FILE,
                        metavar='CONFIG_FILE',
                        help='INI file to read configs (default: {})'.format(CONFIG_FILE))
    parser.add_argument('-d', action='store_true',
                        help='Enable debug output (implies -v)')
    parser.add_argument('-f', default=BOOKS_FILE, metavar='BOOKS_FILE',
                        help='TSV file with the books to be processed (default: {})'.format(BOOKS_FILE))
    parser.add_argument('--html', action='store_true',
                        help='Produce HTML output')
    parser.add_argument('--html-template', default=TEMPLATE_FILE,
                        metavar='TEMPLATE_FILE',
                        help='Template file for the HTML output (default: {})'.format(TEMPLATE_FILE))
    parser.add_argument('-v', action='store_true',
                        help='Enable verbose output')

    args = parser.parse_args()

    config_file = args.config
    config = read_config(config_file)

    config['books_file'] = args.f
    config['cache_file'] = args.cache
    config['html'] = args.html
    config['html_template'] = args.html_template
    config['verbose'] = args.v or args.d
    config['debug'] = args.d

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
