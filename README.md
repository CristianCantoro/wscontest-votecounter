# Wikisource Contest vote counter

A script to count votes for the Wikisource anniversary contest.

## Usage
```bash
usage: score.py [-h] [--cache CACHE_FILE] [--config CONFIG_FILE] [-d]
                [--enable-cache] [-f BOOKS_FILE] [--html]
                [--html-output OUTPUT_HTML] [--html-template TEMPLATE_FILE]
                [-o OUTPUT_TSV] [-v]

Count proofread and validated pages for the Wikisource contest.

optional arguments:
  -h, --help                        show this help message and exit
  --cache CACHE_FILE                JSON file to read and store the cache (default: books_cache.json)
  --config CONFIG_FILE              INI file to read configs (default: contest.conf.ini)
  -d                                Enable debug output (implies -v)
  --enable-cache                    Enable caching
  -f BOOKS_FILE                     TSV file with the books to be processed (default: books.tsv)
  --html                            Produce HTML output
  --html-output OUTPUT_HTML         Output file for the HTML output (default: index.html)
  --html-template TEMPLATE_FILE     Template file for the HTML output (default: index.template.html)
  -o OUTPUT_TSV                     Output file (default: results.tsv)
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
It contains the language of the Wikisource, the start and end dates for the contest.

```
# Confiuration file for the wscontest-votecounter script
# Wikisource anniversary contest of 2015.


[contest]
language = it

# Dates are in the format yyyy-mm-dd
start_date = 2015-11-24
end_date = 2015-12-08
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

## Installation

This script uses Python 3, it has been tested with Python 3.4.3.
It requires only libraries that are part of the standard Python 3 library.

You can install the additional Python module [`yajl`](https://pypi.python.org/pypi/yajl/0.3.5)
([GitHub repo](https://github.com/rtyler/py-yajl/)) for faster reading/writing of JSON.

You can install it using `pip` with the following command:
```bash
pip install -r requirements.txt
```
This has been tested to work also in a virtualenv.

## Processing books in parallel

You can split up your list of books in several files (say `books01.tsv`, `books02.tsv`,
`books03.tsv`, `books04.tsv`) and process them in parallel.

A way to split the original list of books is to use the following commands:
```bash
$ cat books.tsv | grep -v -e "#" | sort | sed '/^$/d' > united
$ split -l 11 --numeric-suffixes=01 --additional-suffix=".tsv" united books
```
The first line creates a list of books removing empty lines and lines starting with `#`
and saves it to a file named `united`. The second line split the content of `united`
in smaller files named `books01.tsv`, `books01.tsv`, etc. with 11 lines per file
(`-l 11` option).

If you split the files by hand, a way to check if the original list (`books.tsv`) and
the new lists contain the same books you can do the following:

```bash
$ cat books.tsv | grep -v -e "#" | sort | sed '/^$/d' > united
$ cat books??.tsv | grep -v -e "#" | sort | sed '/^$/d' > separated
$ diff united separated
```
The first line creates a list of books removing empty lines and lines starting with `#`
and saves it to a file named `united`. The second line does the same for `books01.tsv`, ...,
`books04.tsv` and saves the results in a file named `separated`.
The third line compares the two results. If you split the books in the new lists correctly,
you should see no difference.

You can launch the script on the different input file with the following command
(analogously for `books02.tsv`, `books03.tsv`, `books04.tsv`):
```bash
python score.py -f books01.tsv -o results01.tsv --cache books_cache01.json
```

For best performance you should split the list in a balanced way with respect to the number
of pages to process.

### Merging the results

To merge the results you can use the `merge.py` script.
```
usage: merge.py [-h] [--cache [CACHE_FILE [CACHE_FILE ...]]]
                [--cache-output CACHE_OUTPUT] [-d] [-o OUTPUT_TSV] [-v]
                FILE1 FILE2 ...

Merge results from score.py.

positional arguments:
  FILE1                 Result file no. 1
  FILE2                 Result file no. 2
  ...                   Additional result files

optional arguments:
  -h, --help                                show this help message and exit
  --cache [CACHE_FILE [CACHE_FILE ...]]     Merge cache files
  --cache-output CACHE_OUTPUT               JSON file to store the merged cache (requires --cache)
                                            (default: books_cache_tot.tsv)
  -d                                        Enable debug output (implies -v)
  -o OUTPUT_TSV                             Output file (default: results_tot.tsv)
  -v                                        Enable verbose output
```

Asuming that the results files are named `results01.tsv`, `results02.tsv`, `results03.tsv`
and `results04.tsv` you can merge them with:
```bash
$ python  merge.py results01.tsv results02.tsv results03.tsv results04.tsv
```
the results are written to `results_tot.tsv`
