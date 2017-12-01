#!/bin/sh

set -o errexit

cat data/feedback_corrections.tsv | grep "Submit correction" | awk -F'\t' '{ print $3","$4","$5}' > /tmp/corrections.csv
grep -E "$(cat /tmp/corrections.csv | awk -F, '{ print $1 }' | paste -s -d '|')" /tmp/images.ndjson > /tmp/corrections.ndjson
python oldtoronto/geocode.py --input /tmp/corrections.ndjson --output /tmp/corrections.geocode_results.json
python oldtoronto/corrections_metrics.py
cat /tmp/incorrect.csv
