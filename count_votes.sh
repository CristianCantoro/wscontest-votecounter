#!/usr/bin/env bash

if [ ! -f "books.tsv" ]; then
	echo "This script assumes that the book list is in a file named "
	echo "'books.tsv' in the current directory "
	exit -1
fi

read -p "Number of chuncks to process (1 <= N <= 16)? "
if [ "$REPLY" -lt 1 ]; then 
	REPLY=1;
fi

if [ "$REPLY" -gt 16 ]; then 
	REPLY=16;
fi
NUM_CHUNKS=$REPLY
echo "Processing books in $NUM_CHUNKS chunks."

rm -rf output_dir
rm -f books*_sublist.tsv*
rm -f results*_sublist.tsv*

echo
echo -n "Preparing book lists..."
cat "books.tsv" | grep -v -e "#" | sort | sed '/^$/d' > "united"
NUM_BOOKS=$(wc -l < "united")
BOOKS_PER_FILE=$(expr $NUM_BOOKS / $NUM_CHUNKS + 1)

echo " each list will contain $BOOKS_PER_FILE books"
split -l $BOOKS_PER_FILE --numeric-suffixes=01 --additional-suffix="_sublist.tsv" united books
rm united
NUM_BOOK_LISTS=$(ls -1 books*_sublist.tsv | wc -l)

echo
echo "There are $NUM_BOOK_LISTS sub-lists with $BOOKS_PER_FILE books per list"

echo
echo "***********************************************"
echo "I will launch the parallel processes"
echo "Check the progress with the following command:"
echo
echo "tail -n 3 output_dir/1/*/stderr"
echo
echo "***********************************************"
echo
seq -w 01 $NUM_BOOK_LISTS | parallel -t --files --results output_dir $(which python3) score.py -v -f books{}_sublist.tsv -o results{}_sublist.tsv

echo
echo "Books processed... removing temporary files"
rm -rf output_dir
rm -f books*_sublist.tsv*

echo
echo "Merging results..."
python  merge.py -v results*_sublist.tsv

echo
echo "Done... removing temporary files"
rm results*_sublist.tsv*

echo
echo "All done results are in results_tot.tsv"
