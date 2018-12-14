# generate dataset or contest

all: scores stats submissions


count_votes:
	./count_votes.sh

clean:
	rm -f   books*_sublist.tsv
	rm -f   books*_sublist.tsv.booklist_cache.json
	rm -f   results*_sublist.tsv
	rm -f   united
	rm -rf  output_dir/
