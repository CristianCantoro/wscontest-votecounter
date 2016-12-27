#!/usr/bin/env bash
all=false

read -d '' docstring <<EOF
Usage:
  clean.sh [( -a | --all )]
  clean.sh ( -h | --help )
  clean.sh ( --version )


  Options:
    -a, --all       Delete all files, including results
    -h, --help      Show this help message and exits.
    --version       Print version and copyright information.
----
clean.sh 0.1.0
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

rm -rfv output_dir
rm -fv books*_sublist.tsv*
rm -fv results*_sublist.tsv*
rm -rfv debug
rm -fv united
rm -fv ./*.booklist_cache.json

if $all; then
    rm -fv results_tot.tsv
    rm -fv index.html
fi
