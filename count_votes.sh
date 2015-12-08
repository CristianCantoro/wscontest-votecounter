#!/usr/bin/env bash

read -p "Number of chuncks to process (1 <= N <= 16)? "
if [ "$REPLY" -lt 1 ]; then 
	REPLY=1;
fi

if [ "$REPLY" -gt 16 ]; then 
	REPLY=16;
fi
NUM_CHUNKS=$REPLY
echo "Processing books in $NUM_CHUNKS chunks."

echo
echo -n "Preparing book lists..."
cat "books.tsv" | grep -v -e "#" | sort | sed '/^$/d' > "united"
NUM_BOOKS=$(wc -l < "united")
BOOKS_PER_FILE=$(expr $NUM_BOOKS / $NUM_CHUNKS + 1)

echo " each list will contain $BOOKS_PER_FILE books"
split -l $BOOKS_PER_FILE --numeric-suffixes=01 --additional-suffix=".tsv" "united" "books."
rm united

echo
echo "***********************************************"
echo "I will launch the parallel processes"
echo "Check the progress with the following command:"
echo
echo "tail -n 3 output_dir/1/*/stderr"
echo
echo "***********************************************"
echo
seq -w 01 $NUM_CHUNKS | parallel -t --files --results output_dir "python score.py -v -f books{}.tsv -o results{}.tsv"

echo
echo "Books processed... removing temporary files"
rm -r output_dir
rm -f "books??.tsv*"

echo
echo "Merging results..."
python  merge.py -v "results??.tsv" 

echo
echo "Done... removing temporary files"
rm -f "results??.tsv*"

echo
echo "All done results are in results_tot.tsv"