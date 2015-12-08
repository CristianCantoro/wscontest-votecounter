#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
merge.py
A script to merge results from score.py

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
from collections import defaultdict

### GLOBALS AND DEFAULTS ###
# Files
OUTPUT_TSV = 'results_tot.tsv'
CACHE_OUTPUT = 'books_cache_tot.tsv'

# Globals
CSV_FIELDS = ['user', 'punts', 'vali', 'revi']
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

                if user not in ranking:
                    ranking[user] = {'punts': 0,
                                     'vali': 0,
                                     'revi': 0
                                     }

                ranking[user]['punts'] += punts
                ranking[user]['vali'] += vali
                ranking[user]['revi'] += revi

    return ranking


def get_rows(ranking):
    return [(user,
             ranking[user]['punts'],
             ranking[user]['vali'],
             ranking[user]['revi']
             )
            for user in sorted(ranking.keys(),
                               key=lambda u: ranking[u]['punts'],
                               reverse=True)
            ]


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
    logger.debug("Reading cache")
    with codecs.open(cache_file, 'r', 'utf-8') as f:
        cache = json.load(f)

    return cache


def merge_cache(cachefiles):
    cache = dict()
    booklist = 'CACHE_BOOKS_LIST'
    cache[booklist] = dict()

    for cachef in cachefiles:
        cache_part = read_cache(cachef)

        cache[booklist].update(cache_part[booklist])
        for key in cache.keys():
            if key == booklist:
                continue
            cache[key] = cache_part[key]

    return cache


def write_cache(cache, cache_output):
    logger.debug("Writing cache")
    with codecs.open(cache_output, 'w', 'utf-8') as f:
        json.dump(cache, f)


def main(resfiles, config):

    output = config['output']
    ranking = get_ranking(resfiles)
    write_results(ranking, output)

    if config['cache']:
        cachefiles = config['cache']
        cache_output = config['cache_output']
        cache = merge_cache(cachefiles)
        write_cache(cache, cache_output)


if __name__ == '__main__':

    DESCRIPTION = 'Merge results from score.py.'
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument('resfile1', metavar='FILE1',
                        help='Result file no. 1')
    parser.add_argument('resfile2', metavar='FILE2',
                        help='Result file no. 2')
    parser.add_argument('resfile_others', metavar='...', nargs=argparse.REMAINDER,
                        help='Additional result files')
    parser.add_argument('--cache', nargs='*', metavar='CACHE_FILE',
                        help='Merge cache files')
    parser.add_argument('--cache-output', default=CACHE_OUTPUT, metavar='CACHE_OUTPUT',
                        help='JSON file to store the merged cache (requires --cache) (default: {})'.format(CACHE_OUTPUT))
    parser.add_argument('-d', action='store_true',
                        help='Enable debug output (implies -v)')
    parser.add_argument('-o', default=OUTPUT_TSV, metavar='OUTPUT_TSV',
                        help='Output file (default: {})'.format(OUTPUT_TSV))
    parser.add_argument('-v', action='store_true',
                        help='Enable verbose output')

    args = parser.parse_args()

    resfiles = list()

    resfiles.append(args.resfile1)
    resfiles.append(args.resfile2)
    if args.resfile_others:
        resfiles = resfiles + args.resfile_others

    config = dict()
    config['cache'] = args.cache
    config['cache_output'] = args.cache_output
    config['output'] = args.o
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