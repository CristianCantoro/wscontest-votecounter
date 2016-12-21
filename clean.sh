#!/usr/bin/env bash
# bash strict mode
# See:
# http://redsymbol.net/articles/unofficial-bash-strict-mode/
set -euo pipefail
IFS=$'\n\t'

rm -rfv output_dir
rm -fv books*_sublist.tsv*
rm -fv results*_sublist.tsv*
rm -rfv debug
rm -fv ./*.booklist_cache.json
