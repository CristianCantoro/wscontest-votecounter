#!/usr/bin/env bash
# bash strict mode
set -euo pipefail
IFS=$'\n\t'

debug_dir="$1"

function sumcol() {
    local stringarr=''
    while read -r line; do
        stringarr+=("$line")
    done

    echo "${stringarr[*]}" | awk '{SUM+=$1} END {print SUM}'
}

find "$debug_dir" -maxdepth 1 -type f -name '*.csv' | while read filename; do
    echo -en "$(basename "$filename")\t"

    res=$(tail -n+2 "$filename" | awk -F'\t' '{print $2}' | sort | uniq -c)

    alltime_dup=0
    contest_dup=0
    contest_single=0

    # echo
    # echo "$res"
    # echo "---"

    if echo "$res" | grep -E '(C|D)' &>/dev/null; then
        alltime_dup=$( echo "$res" | grep -E '(C|D)' | sumcol )
    fi

    if echo "$res" | grep 'C' &>/dev/null; then
        contest_dup=$(echo "$res" | grep 'C' | sumcol )
    fi

    alltime_single=$(echo "$res" | sumcol )

    if echo "$res" | grep -E '(C|P)' &>/dev/null; then
        contest_single=$(echo "$res" | grep -E '(C|P)' | sumcol )
    fi

    echo -e "$alltime_dup\t$contest_dup\t$alltime_single\t$contest_single"

done
