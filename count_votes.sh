#!/usr/bin/env bash

debug=false
verbose=true
quiet=false
man=false
no_keep_files=false

book_file=''
config=''
num_chunks=1
num_jobs=1

read -rd '' docstring <<EOF
Usage:
  count_votes.sh [options] [ --debug | --quiet ]
  count_votes.sh ( -h | --help )
  count_votes.sh ( --version )


  Options:
    -b, --book-file BOOK_FILE       Book file [default: books.tsv].
    -c, --config CONFIG             Config file [default: contest.conf.ini].
    -n, --num-chunks NUM_CHUNKS     Number of chunks to process [default: 1].
    -j, --num-jobs NUM_JOBS         Number of parallel jobs [default: NUM_CHUNKS].
    -d, --debug                     Enable debug mode (incompatible with --quiet).
    -K, --no-keep-files             Delete temporary files.
    -q, --quiet                     Suppress console output.
    --man                           Display a man page.
    -h, --help                      Show this help message and exits.
    --version                       Print version and copyright information.
----
count_votes.sh 0.3.0
copyright (c) 2019 Cristian Consonni
MIT License
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.
EOF

eval "$(echo "$docstring" | docopts -V - -h - : "$@" )"

# bash strict mode
# See:
# https://balist.es/blog/2017/03/21/enhancing-the-unofficial-bash-strict-mode/
# shellcheck disable=SC2128
SOURCED=false && [ "$0" = "$BASH_SOURCE" ] || SOURCED=true

if ! $SOURCED; then
  set -euo pipefail
  IFS=$'\n\t'
fi

# --debug is incompatible with --quiet
# this is already handled by docopts, I leave it here for clarity
if $debug && $quiet; then
  (>&2 echo "Options --debug and --quiet are incompatible")
  exit 1
fi

#################### Utils
function echodebug() { true; }
function echoverbose() {
  echo "$@"
}

if $debug; then
  function echodebug() {
      echo -en "[$(date '+%F_%k:%M:%S')][debug]\t"
      echo "$@" 1>&2;
  }
fi

if $quiet; then
  function echoverbose() { true; }
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

if [ "$num_jobs" == "NUM_CHUNKS" ]; then
  num_jobs="$num_chunks" 
fi

echodebug "book_file: $book_file"
echodebug "config_file: $config"
echodebug "num_chunks: $num_chunks"
echodebug "num_jobs: $num_jobs"

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
echoverbose "Preparing book lists..."
grep -v -e "#" "${book_file}" | sort | sed '/^$/d' > 'united'
NUM_BOOKS=$(wc -l < 'united')

echodebug "NUM_BOOKS: $NUM_BOOKS"
echodebug "num_chunks: $num_chunks"

if ((NUM_BOOKS % num_chunks)); then
  BOOKS_PER_FILE=$((NUM_BOOKS/num_chunks+1))
else
  BOOKS_PER_FILE=$((NUM_BOOKS/num_chunks))
fi

echoverbose "Each list will contain $BOOKS_PER_FILE books"
split -l "$BOOKS_PER_FILE" \
    --numeric-suffixes=01 \
    --additional-suffix="_sublist.tsv" \
    'united' books

if $no_keep_files; then
  rm -f 'united'
fi
NUM_BOOK_LISTS=$(find . -mindepth 1 -maxdepth 1 -name 'books*_sublist.tsv' \
                 | wc -l)

echoverbose
echoverbose "There are $NUM_BOOK_LISTS sub-lists with $BOOKS_PER_FILE books per list"

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

parallel_verbosity='--eta'
if ! $verbose; then
  parallel_verbosity='--bar'
fi

set +e
# score.py process can end with:
#   src/tcmalloc.cc:278] Attempt to free invalid pointer
# disabling -e while we figure out this problem.
seq -w 01 "$NUM_BOOK_LISTS" | \
    parallel "$print_processes_flag" "$files_flag" \
        --jobs "$num_jobs" \
        ${parallel_verbosity} \
        --results output_dir \
        "$(command -v python3)" score.py "$verbosity" \
            --config "$config" \
            -f books{}_sublist.tsv \
            -o results{}_sublist.tsv
set -e

echoverbose
echoverbose -n "Books processed... "
if $no_keep_files; then
  echoverbose "removing temporary files"
  rm -rf output_dir
  rm -f books*_sublist.tsv*
fi
echoverbose

echoverbose
echoverbose "Merging results..."
$(command -v python3)  merge.py \
   "$verbosity" \
   --config "$config" \
   --html \
   --html-output index.html \
     results*_sublist.tsv

echoverbose
echoverbose -n "Done... "
if $no_keep_files; then
  echoverbose "removing temporary files"
  rm -f results*_sublist.tsv*
fi
echoverbose

echoverbose
echoverbose "All done results are in results_tot.tsv"
