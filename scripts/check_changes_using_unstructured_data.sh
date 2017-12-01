#!/bin/bash
# take a file with image ids that you want to check in the second column and generate some geojson files highlighting changes
set -o errexit

original_geojson="data/2018-03-20-launch.images.geojson"

if [[ ! -f data/unstructured_feedback.tsv ]] ;
then
	echo 'File "data/unstructured_feedback.tsv" does not exist, ensure it exists and has image ids in the second column.'
	exit
fi

python oldtoronto/geocode.py --ids "$(cat data/unstructured_feedback.tsv | awk -F'\t' '{ print $2}' | paste -s -d ',')" --output /tmp/geocodes.json
python oldtoronto/generate_geojson.py --geocode_results /tmp/geocodes.json --output /tmp/images.geojson
python oldtoronto/diff_geojson.py --sample_set "$(cat data/unstructured_feedback.tsv | awk -F'\t' '{ print $2}' | paste -s -d '|')" "${original_geojson}" /tmp/images.geojson --num_samples 10
echo "estimation of the number of corrected geocodes: $(jq '.features | length' /tmp/changed.geojson)"
echo "estimation of the number of geocodes remaining incorrect: $(jq '.features | length' /tmp/unchanged.geojson)"
