# Wikisource Contest vote counter

A script to count votes for the Wikisource anniversary contest.

## Usage
```bash
usage: score.py [-h] [--cache CACHE_FILE] [--config CONFIG_FILE] [-d]
                [-f BOOKS_FILE] [--html] [--html-output OUTPUT_HTML]
                [--html-template TEMPLATE_FILE] [-o OUTPUT_TSV] [-v]

Count proofread pages for the Wikisource contest.

optional arguments:
  -h, --help                        show this help message and exit
  --cache CACHE_FILE                JSON file to read and store the cache (default: books_cache.json)
  --config CONFIG_FILE              INI file to read configs (default: contest.conf.ini)
  -d                                Enable debug output (implies -v)
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

To empty the cache delete the file. You can also remove individual books, you
can use the [jq utility](https://stedolan.github.io/jq) to pretty-print the file
and then modify it with any text editor or you can use an on-line tool such as
[JSONlint](http://jsonlint.com/).

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
