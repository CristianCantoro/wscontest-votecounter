# Wikisource Contest vote counter

A collection of scripts to count votes for the Wikisource anniversary contest.

## Usage
```bash
usage: score.py [-h] [--booklist-cache BOOKLIST_CACHE] [--cache CACHE_FILE]
                [--config CONFIG_FILE] [-d] [--enable-cache] [-f BOOKS_FILE]
                [-o OUTPUT_TSV] [-v]

Count proofread and validated pages for the Wikisource contest.

optional arguments:
  -h, --help                        show this help message and exit
  --booklist-cache BOOKLIST_CACHE   JSON file to read and store the booklist cache
                                    (default: {BOOKS_FILE}.booklist_cache.json)
  --cache CACHE_FILE                JSON file to read and store the cache
                                    (default: {BOOKS_FILE}.cache.json)
  --config CONFIG_FILE              INI file to read configs (default: contest.conf.ini)
  -d                                Enable debug output (implies -v)
  --enable-cache                    Enable caching
  -f BOOKS_FILE                     TSV file with the books to be processed
                                    (default: books.tsv)
  -o OUTPUT_TSV                     Output file (default: {BOOKS_FILE}.results.tsv)
  -v                                Enable verbose output

```

### Input
The script expect to read two files:
* `books.tsv`
* `contest.conf.ini`

#### books.tsv
`books.tsv` a list of books. The number of pages is requested to the API and the response is cached.
Here's a sample:
```
# List of books participating in the Wikisource anniversary contest of 2015.
#
# FORMAT
# book_name
#
# Empty lines or lines starting with "#" are ignored.

"Bandello - Novelle, Laterza 1910, I.djvu"
```

#### contest.conf.ini
`contest.conf.ini` is INI-like configuration file.
It contains the following parameters:

* `rules_page`: the page with the list of books participating in the contest, usually this page also hosts the rules
* `language`: language of the Wikisource
* `start_date` and `end_date`: respectively the start and end dates for the contest.
* `book_regex`: a regular expression specifying how to search for the title of books participating in the contest (used by `extract_books.py`)

```
# Confiuration file for the wscontest-votecounter script
# Wikisource anniversary contest of 2017.

[contest]
rules_page = Wikisource:Quattordicesimo compleanno di Wikisource
language = it

# Dates are in the format yyyy-mm-dd HH:MM:SS.
# Times are in UTC
start_date = 2017-11-24 00:00:00
end_date = 2017-12-08 23:59:59

# regex used to search for books participating in the contest
book_regex = \[\[File:(.+?)\.(djvu|pdf)\|?.*?\]\]
```

### Extract the book list

You can use the script `extract_books.py` to get the list of books
participating in the contest.

```bash
Usage:
    extract_books.py [-h] [--config CONFIG_FILE] [-d] [-o BOOKS_FILE] [-v]

Extract the list of books valid for the Wikisource contest.

optional arguments:
  -h, --help            show this help message and exit
  --config CONFIG_FILE  INI file to read configs (default: contest.conf.ini)
  -d, --debug           Enable debug output (implies -v)
  -o BOOKS_FILE         TSV file with the books to be processed (default:
                        books.tsv)
  -v, --verbose         Enable verbose output
```

### Cache
The scripts queries the Wikisource API and counts the number of pages that have
been proofread by a user.

Results for every single book are cached in a JSON file called `books_cache.json`.

Keep in mind that caching slows down the script (because the cache is continuosly
read and written), for this reason caching is can be optionally enabled with the
option `--enable-caching`.

To empty the cache delete the cache file.

You can also remove individual books, you can use the [jq utility](https://stedolan.github.io/jq)
to pretty-print the file and then modify it with any text editor or you can use
an on-line tool such as [JSONlint](http://jsonlint.com/).

Here's a example of cached results for a book: 
```json
{
  "CACHE_BOOKS_LIST": {
    "Fineo - Il rimedio infallibile.djvu": 90,
    "Racconti sardi.djvu": 168,
    "Slataper - Il mio carso, 1912.djvu": 124
  }
  "Slataper - Il mio carso, 1912.djvu": {
    "72": {
      "query": {
        "normalized": [
          {
            "from": "Page:Slataper - Il mio carso, 1912.djvu/72",
            "to": "Pagina:Slataper - Il mio carso, 1912.djvu/72"
          }
        ],
        "pages": {
          "412498": {
            "title": "Pagina:Slataper - Il mio carso, 1912.djvu/72",
            "ns": 108,
            "revisions": [
              {
                "contentformat": "text/x-wiki",
                "contentmodel": "proofread-page",
                "timestamp": "2015-12-04T13:32:34Z",
                "user": "Robybulga",
                "*": "...>"
              },
              {
                "contentformat": "text/x-wiki",
                "contentmodel": "proofread-page",
                "timestamp": "2015-11-25T07:50:05Z",
                "user": "Stefano mariucci",
                "*": "..."
              },
              {
                "contentformat": "text/x-wiki",
                "contentmodel": "proofread-page",
                "timestamp": "2015-09-02T18:33:12Z",
                "user": "Phe-bot",
                "*": "..."
              }
            ],
            "pageid": 412498
          }
        }
      },
      "batchcomplete": ""
    }
}
```

### Output
Results are written in TSV format in `results.tsv`. Activating the `--html` flag you can
also produce an HTML version of the output `index.html`.
The HTML output uses a template `index.template.html` that expects to find a `{{{rows}}}`
token to indicate where results will be written.

If you need to produce a Wikitable from the TSV output, you can use one of this tools:
* [CSV to Wikitable](http://mlei.net/shared/tool/csv-wiki.htm)
* [Excel 2 Wiki](http://excel2wiki.net/) (if you open the TSV as a spreadsheet)

## Installation

This script uses Python 3, it has been tested with Python 3.4 and Python 3.5 (up to v. 3.5.2).
It requires only libraries that are part of the standard Python 3 library.

You can install the additional Python module [`yajl`](https://pypi.python.org/pypi/yajl/0.3.5)
([GitHub repo](https://github.com/rtyler/py-yajl/)) for faster reading/writing of JSON.

You can install it using `pip` with the following command:
```bash
pip install -r requirements.txt
```
This has been tested to work in a virtualenv.

## Processing books in parallel

You can use the script `count_votes.sh` to process books in parallel,
The script assumes you have [GNU parallel](https://www.gnu.org/software/parallel/)
and [docopts](https://github.com/docopt/docopts) - which in turn requires the
Python module [docopt](https://github.com/docopt/docopts) - installed on your system.

### count_votes.sh explained

First, we split up the list of books in several files (say `books01_sublist.tsv`,
`books02_sublist.tsv`, `books03_sublist.tsv`, `books04_sublist.tsv`) to process them in
parallel.

The splitting of the original list of books is obtained with the following commands:
```bash
$ cat books.tsv | grep -v -e "#" | sort | sed '/^$/d' > united
$ split -l 11 --numeric-suffixes=01 --additional-suffix="_sublist.tsv" united books
```
The first line creates a list of books removing empty lines and lines starting with `#`
and saves it to a file named `united`. The second line split the content of `united`
in smaller files named `books01_sublist.tsv`, `books02_sublist.tsv`, etc. with up to
11 lines per file (`-l 11` option).

If you split the files by hand, a way to check if the original list (`books.tsv`) and
the new lists contain the same books you can do the following:

```bash
$ cat books.tsv | grep -v -e "#" | sort | sed '/^$/d' > united
$ cat books*_sublist.tsv | grep -v -e "#" | sort | sed '/^$/d' > separated
$ diff united separated
```
The first line creates a list of books removing empty lines and lines starting with `#`
and saves it to a file named `united`. The second line does the same for `books01_sublist.tsv.tsv`,
`...`, `books04_sublist.tsv` and saves the results in a file named `separated`.
The third line compares the two results. If you split the books in the new lists correctly,
you should see no difference.

You can launch the script on the different input file with the following command
(analogously for `books02_sublist.tsv`, `books03_sublist.tsv`, `books04_sublist.tsv`):
```bash
python score.py -f books01_sublist.tsv
```

For best performance you should split the list in a balanced way with respect to the number
of pages to process.

Using [GNU parallel](https://www.gnu.org/software/parallel/) we can launch several processes in
parallel.

Following our example, to process `books01_sublist.tsv`, `...`, `books04_sublist.tsv` in parallel:
```bash
$ seq -w 01 04 | parallel -t --files --results output_dir $(which python3) score.py -v -f books{}_sublist.tsv -o results{}_sublist.tsv
```
The results will be saved in files `results01_sublist.tsv`, `...`, `results04_sublist.tsv`.

You can check the progress of each process with the command:
```bash
$ tail -n 3 output_dir/1/*/stderr
```
or to have a dynamic picture of the situation:
```bash
$ watch -n 1 tail -n 3 output_dir/1/*/stderr
```

The results are merged using the `merge.py` script.

### Merging the results

To merge the results you can use the `merge.py` script.
```
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
  -h, --help                                        show this help message and exit
  --booklist [BOOKLIST_FILE [BOOKLIST_FILE ...]]    Merge booklist cache files
  --booklist-output BOOKLIST_OUTPUT                 JSON file to store the merged cache (requires --booklist)
                                                    (default: booklist_cache_tot.tsv)
  --cache [CACHE_FILE [CACHE_FILE ...]]             Merge cache files
  --cache-output CACHE_OUTPUT                       JSON file to store the merged cache (requires --cache)
                                                    (default: books_cache_tot.tsv)
  --config CONFIG_FILE  INI file to read configs    (default: contest.conf.ini)
  -d                                                Enable debug output (implies -v)
  -o OUTPUT_TSV                                     Output file (default: results_tot.tsv)
  --html                                            Produce HTML output
  --html-output OUTPUT_HTML                         Output file for the HTML output
                                                    (default: {OUTPUT_TSV}.index.html)
  --html-template TEMPLATE_FILE                     Template file for the HTML output
                                                    (default: index.template.html)
  -v                                                Enable verbose output
```

Assuming that the results files are named `results01_sublist.tsv`, `results02_sublist.tsv`,
`results03_sublist.tsv` and `results04_sublist.tsv` as from the previous section,
you can merge them with the following command:
```bash
$ python  merge.py results*_sublist.tsv
```
the results are written to `results_tot.tsv`
