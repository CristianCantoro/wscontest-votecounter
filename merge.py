#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
merge.py
A script to merge results from score.py

---
usage: merge.py [-h] [--booklist [BOOKLIST_FILE [BOOKLIST_FILE ...]]]
                [--booklist-output BOOKLIST_OUTPUT]
                [--cache [CACHE_FILE [CACHE_FILE ...]]]
                [--cache-output CACHE_OUTPUT] [--config CONFIG_FILE] [-d]
                [-o OUTPUT_TSV] [--html] [--html-output OUTPUT_HTML]
                [--html-template TEMPLATE_FILE] [-v]
                FILE1 ...

Merge results from score.py.

positional arguments:
  FILE1                 Result file no. 1
  ...                   Additional result files

optional arguments:
  -h, --help            show this help message and exit
  --booklist [BOOKLIST_FILE [BOOKLIST_FILE ...]]
                        Merge booklist cache files
  --booklist-output BOOKLIST_OUTPUT
                        JSON file to store the merged cache (requires
                        --booklist) (default: booklist_cache_tot.tsv)
  --cache [CACHE_FILE [CACHE_FILE ...]]
                        Merge cache files
  --cache-output CACHE_OUTPUT
                        JSON file to store the merged cache (requires --cache)
                        (default: books_cache_tot.tsv)
  --config CONFIG_FILE  INI file to read configs (default: contest.conf.ini)
  -d                    Enable debug output (implies -v)
  -o OUTPUT_TSV         Output file (default: results_tot.tsv)
  --html                Produce HTML output
  --html-output OUTPUT_HTML
                        Output file for the HTML output (default:
                        {OUTPUT_TSV}.index.html)
  --html-template TEMPLATE_FILE
                        Template file for the HTML output (default:
                        index.template.html)
  -v                    Enable verbose output

---
The MIT License (MIT)

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
import csv
import json
import codecs
import logging
import argparse
import configparser
from html import escape
from collections import defaultdict

### GLOBALS AND DEFAULTS ###
# Files
OUTPUT_TSV = 'results_tot.tsv'
BOOKLIST_OUTPUT = 'booklist_cache_tot.tsv'
CACHE_OUTPUT = 'books_cache_tot.tsv'
CONFIG_FILE = "contest.conf.ini"
TEMPLATE_FILE = "index.template.html"
OUTPUT_HTML = '{OUTPUT_TSV}.index.html'


# Globals
CSV_FIELDS = ['user', 'punts', 'vali', 'revi', 'revi2', 'revi3', 'revi5']
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


def get_ranking(resfiles):
    ranking = dict()

    for resf in resfiles:
        logger.info("Processing file: {}...".format(resf))
        with open(resf, 'r') as csvfile:
            reader = csv.DictReader(csvfile,
                                    fieldnames=CSV_FIELDS,
                                    delimiter='\t')

            firstline = True
            for row in reader:
                if firstline:
                    firstline = False
                    continue

                user = row['user']
                punts = int(row['punts'])
                vali = int(row['vali'])
                revi = int(row['revi'])
                revi2 = int(row['revi2'])
                revi3 = int(row['revi3'])
                revi5 = int(row['revi5'])

                if user not in ranking:
                    ranking[user] = {'punts': 0,
                                     'vali': 0,
                                     'revi': 0,
                                     'revi2': 0,
                                     'revi3': 0,
                                     'revi5': 0
                                     }

                ranking[user]['punts'] += punts
                ranking[user]['vali'] += vali
                ranking[user]['revi'] += revi
                ranking[user]['revi2'] += revi2
                ranking[user]['revi3'] += revi3
                ranking[user]['revi5'] += revi5

    return ranking


def get_rows(ranking):
    # sorting:
    # results are ordered by:
    # (punts desc, revi desc, vali desc, username asc)
    # to obtain this first first sort by username ascending, then by
    # (punts, revi, vali) descending
    return [(user,
             ranking[user]['punts'],
             ranking[user]['vali'],
             ranking[user]['revi'],
             ranking[user]['revi2'],
             ranking[user]['revi3'],
             ranking[user]['revi5']
             )
            for user in sorted(sorted(ranking.keys()),
                               key=lambda u: (ranking[u]['punts'],
                                              ranking[u]['revi'],
                                              ranking[u]['vali']),
                               reverse=True)]



def format_user(name, lang):
    user_string = '<a href="//{lang}.wikisource.org/wiki/User:{name}">{name}</a>'
    return user_string.format(lang=lang, name=escape(name))


def get_html_rows(ranking, lang):
    table_string = '''
    <tr>
    <td>{user}</td>
    <td>{punts}</td>
    <td>{vali}</td>
    <td>{revi}</td><td>{revi2}</td><td>{revi3}</td><td>{revi5}</td>
    </tr>'''
    return [table_string.format(user=format_user(user, lang),
                                punts=user_punts,
                                vali=user_vali,
                                revi=user_revi,
                                revi2=user_revi2,
                                revi3=user_revi3,
                                revi5=user_revi5,
                                )
            for user, user_punts, user_vali, user_revi, \
                user_revi2, user_revi3, user_revi5,
            in get_rows(ranking)]


def write_html(ranking, lang, html_template, output_html):
    with open(html_template, 'r') as f:
        template = f.read()

    html_rows = get_html_rows(ranking, lang=lang)
    content = template.replace("{{{rows}}}", '\n'.join(html_rows))
    with codecs.open(output_html, 'w', 'utf-8') as f:
        f.write(content)


def write_results(ranking, output):
    with open(output, 'w') as csvfile:
        writer = csv.DictWriter(csvfile,
                                fieldnames=CSV_FIELDS,
                                delimiter='\t',
                                quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()

        rows = get_rows(ranking)

        for row in rows:
            writer.writerow(dict(zip(CSV_FIELDS, row)))


def read_cache(cache_file):
    logger.debug("Reading cache: {}".format(cache_file))
    with codecs.open(cache_file, 'r', 'utf-8') as f:
        cache = json.load(f)

    return cache


def merge_cache(cachefiles):
    cache = dict()

    for cachef in cachefiles:
        cache_part = read_cache(cachef)

        for key in cache_part.keys():
            if key not in cache:
                cache[key] = cache_part[key]
            else:
                cache[key].update(cache_part[key])

    return cache


def write_cache(cache, cache_output):
    logger.debug("Writing cache: {}".format(cache_output))
    with codecs.open(cache_output, 'w', 'utf-8') as f:
        json.dump(cache, f)


def read_config(config_file):
    config = {}
    parser = configparser.ConfigParser()
    parser.read(config_file)

    config['contest'] = dict([(k ,v) for k, v in parser['contest'].items()])
    return config


def main(resfiles, config):

    output = config['output']

    ranking = get_ranking(resfiles)
    write_results(ranking, output)

    if config['html']:
        lang = config['contest']['language']
        output_html = config['html_output']
        html_template = config['html_template']
        write_html(ranking, lang, html_template, output_html)

    if config['cache']:
        cachefiles = config['cache']
        cache_output = config['cache_output']
        cache = merge_cache(cachefiles)
        write_cache(cache, cache_output)

    if config['booklist']:
        booklistfiles = config['booklist']
        booklist_output = config['booklist_output']
        booklist = merge_cache(booklistfiles)
        write_cache(booklist_output)


if __name__ == '__main__':

    DESCRIPTION = 'Merge results from score.py.'
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument('resfile1', metavar='FILE1',
                        help='Result file no. 1')
    parser.add_argument('resfile_others', metavar='...', nargs=argparse.REMAINDER,
                        help='Additional result files')
    parser.add_argument('--booklist', nargs='*', metavar='BOOKLIST_FILE',
                        help='Merge booklist cache files')
    parser.add_argument('--booklist-output', default=BOOKLIST_OUTPUT, metavar='BOOKLIST_OUTPUT',
                        help='JSON file to store the merged cache (requires --booklist) (default: {})'.format(BOOKLIST_OUTPUT))
    parser.add_argument('--cache', nargs='*', metavar='CACHE_FILE',
                        help='Merge cache files')
    parser.add_argument('--cache-output', default=CACHE_OUTPUT, metavar='CACHE_OUTPUT',
                        help='JSON file to store the merged cache (requires --cache) (default: {})'.format(CACHE_OUTPUT))
    parser.add_argument('--config', default=CONFIG_FILE, metavar='CONFIG_FILE',
                        help='INI file to read configs (default: {})'.format(CONFIG_FILE))
    parser.add_argument('-d', action='store_true',
                        help='Enable debug output (implies -v)')
    parser.add_argument('-o', default=OUTPUT_TSV, metavar='OUTPUT_TSV',
                        help='Output file (default: {})'.format(OUTPUT_TSV))
    parser.add_argument('--html', action='store_true',
                        help='Produce HTML output')
    parser.add_argument('--html-output', default=OUTPUT_HTML, metavar='OUTPUT_HTML',
                        help='Output file for the HTML output (default: {})'.format(OUTPUT_HTML))
    parser.add_argument('--html-template', default=TEMPLATE_FILE, metavar='TEMPLATE_FILE',
                        help='Template file for the HTML output (default: {})'.format(TEMPLATE_FILE))
    parser.add_argument('-v', action='store_true',
                        help='Enable verbose output')

    args = parser.parse_args()

    resfiles = list()

    resfiles.append(args.resfile1)
    if args.resfile_others:
        resfiles = resfiles + args.resfile_others

    config_file = args.config
    config = read_config(config_file)

    config['booklist'] = args.booklist
    config['booklist_output'] = args.booklist_output
    config['cache'] = args.cache
    config['cache_output'] = args.cache_output

    # tsv output
    config['output'] = args.o

    # HTML output
    config['html'] = args.html
    config['html_template'] = args.html_template
    if "OUTPUT_TSV" in args.html_output:
        config['html_output'] = args.html_output.format(
            OUTPUT_TSV=config['output'])
    else:
        config['html_output'] = args.html_output

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
    logger.debug(resfiles)

    main(resfiles, config)