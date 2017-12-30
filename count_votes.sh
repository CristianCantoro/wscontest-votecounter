#!/usr/bin/env bash

debug=false
verbose=false
man=false
keep_files=false

book_file=''
num_chunks=1

read -rd '' docstring <<EOF
Usage:
  count_votes.sh [options]
  count_votes.sh ( -h | --help )
  count_votes.sh ( --version )


  Options:
    -b, --book-file BOOK_FILE       Book file [default: books.tsv]
    -n, --num-chunks NUM_CHUNKS     Number of chunks to process [default: 1]
    -d, --debug                     Enable debug mode (implies --verbose)
    -k, --keep-files                Do not delete temporary files.
    -v, --verbose                   Generate verbose output.
    --man                           Display a man page.
    -h, --help                      Show this help message and exits.
    --version                       Print version and copyright information.
----
count_votes.sh 0.1.0
copyright (c) 2016 Cristian Consonni
MIT License
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.
EOF

eval "$(echo "$docstring" | docopts -V - -h - : "$@" )"

# bash strict mode
# See:
# http://redsymbol.net/articles/unofficial-bash-strict-mode/
set -euo pipefail
IFS=$'\n\t'

# --debug implies --verbose
if $debug; then
  verbose=true
fi

#################### Utils
function echodebug() { true; }
function echoverbose() { true; }

if $debug; then
    function echodebug() {
        echo -en "[$(date '+%F_%k:%M:%S')][debug]\t"
        echo "$@" 1>&2;
    }
fi

if $verbose; then
    function echoverbose() {
        echo "$@"
    }
fi

bold()          { ansi 1 "$@"; }
italic()        { ansi 3 "$@"; }
underline()     { ansi 4 "$@"; }
strikethrough() { ansi 9 "$@"; }
ansi()          { echo -e "\\e[${1}m${*:2}\\e[0m"; }
####################


#################### Documentation helpers

function print_help() {
  eval "$(echo "$docstring" | docopts -V - -h - : '-h' | head -n -1)"
}

function print_man() {

  print_help

  echo -e "$(cat <<MANPAGE

$(bold THIS\ MANPAGE\ NEEDS\ TO\ BE\ WRITTEN)

MANPAGE
)"

}

if $man; then
  print_man
  exit 0
fi

echodebug "book_file: $book_file"
echodebug "num_chunks: $num_chunks"

if [ ! -f "$book_file" ]; then
    (>&2 echo "This script assumes that the book list is in a file named: ")
    (>&2 echo "'$book_file'")
    exit 1
fi

echoverbose "Processing books in $num_chunks chunks."

rm -rf output_dir
rm -f books*_sublist.tsv*
rm -f results*_sublist.tsv*

echoverbose
echoverbose -n "Preparing book lists..."
grep -v -e "#" "${book_file}" | sort | sed '/^$/d' > 'united'
NUM_BOOKS=$(wc -l < 'united')
BOOKS_PER_FILE=$((NUM_BOOKS/num_chunks+1))

echoverbose " each list will contain $BOOKS_PER_FILE books"
split -l $BOOKS_PER_FILE \
    --numeric-suffixes=01 \
    --additional-suffix="_sublist.tsv" \
    'united' books

if ! $keep_files; then
  rm 'united'
fi
NUM_BOOK_LISTS=$(find . -name 'books*_sublist.tsv' | wc -l)

echoverbose
echoverbose "There are $NUM_BOOK_LISTS sub-lists with"
echoverbose "$BOOKS_PER_FILE books per list"

echoverbose
echoverbose "***********************************************"
echoverbose "Launching the parallel processes"
echoverbose "Check the progress with the following command:"
echoverbose
echoverbose "tailf output_dir/1/*/stderr"
echoverbose
echoverbose "***********************************************"
echoverbose

verbosity=''
print_processes_flag=''
files_flag=''
if $verbose; then
    verbosity='--verbose'
    print_processes_flag='-t'
    files_flag='--files'
    if $debug; then
        verbosity='--debug'
    fi
fi

if $verbose; then
    seq -w 01 "$NUM_BOOK_LISTS" | \
        parallel "$print_processes_flag" "$files_flag" \
            --eta \
            --results output_dir \
            "$(which python3)" score.py "$verbosity" \
                -f books{}_sublist.tsv \
                -o results{}_sublist.tsv
else
    seq -w 01 "$NUM_BOOK_LISTS" | \
        parallel --bar --results output_dir \
            "$(which python3)" score.py \
                -f books{}_sublist.tsv \
                -o results{}_sublist.tsv
fi

echoverbose
echoverbose -n "Books processed... "
if ! $keep_files; then
  echoverbose "removing temporary files"
  rm -rf output_dir
  rm -f books*_sublist.tsv*
fi
echoverbose

echoverbose
echoverbose "Merging results..."
$(which python3)  merge.py "$verbosity" --html --html-output index.html \
    results*_sublist.tsv

echoverbose
echoverbose -n "Done... "
if ! $keep_files; then
  echoverbose "removing temporary files"
  rm -f results*_sublist.tsv*
fi
echoverbose

echoverbose
echoverbose "All done results are in results_tot.tsv"
