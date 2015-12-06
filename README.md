# Wikisource Contest vote counter

A script to count votes for the Wikisource anniversary contest.

## Usage
```
usage: score.py [-h] [--cache CACHE_FILE] [--config CONFIG_FILE] [-d]
                [-f BOOKS_FILE] [--html] [--html-template TEMPLATE_FILE] [-v]

Count proofread pages for the Wikisource contest.

optional arguments:
  -h, --help            			show this help message and exit
  --cache CACHE_FILE    			JSON file to read and store the cache (default: books_cache.json)
  --config CONFIG_FILE  			INI file to read configs (default: contest.conf.ini)
  -d                    			Enable debug output (implies -v)
  -f BOOKS_FILE         			TSV file with the books to be processed (default: books.tsv)
  --html 				            Produce HTML output
  --html-template TEMPLATE_FILE		Template file for the HTML output (default: index.template.html)
  -v                    			Enable verbose output
```

### Input
The script expect to read two files:
* `books.tsv`
* `contest.conf.ini`

#### books.tsv
`books.tsv` a tab-separated list of books. Here's a sample:

```
# List of books participating in the Wikisource anniversary contest of 2015.
#
# FORMAT
# book_name		num_pages
#
# Fields are separated tabs (\t). You can use as many tabs as you like.
# 
# Empty lines or lines starting with "#" are ignored.

"Bandello - Novelle, Laterza 1910, I.djvu"		426
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
  "Fineo - Il rimedio infallibile.djvu": {
    "punts": {
      "BluesBrothers": 2,
      "Zuleika72": 4,
      "Luigi62": 38,
      "Robybulga": 22,
      "Sannita (ICCU)": 16
    },
    "revi": {
      "BluesBrothers": 1,
      "Zuleika72": 2,
      "Luigi62": 19,
      "Robybulga": 11,
      "Sannita (ICCU)": 8
    },
    "vali": {}
  }
}
```
## Installation

This script uses Python 3, it has been tested with Python 3.4.3.
It requires only libraries that are part of the standard Python 3 library.
