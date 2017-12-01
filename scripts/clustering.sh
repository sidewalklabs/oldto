#!/bin/sh
# change the viewport location in oldto-site/js/viewer.js
# change the variable location in this script accordingly
# make sure you are serving the files from oldto-site
set -o errexit
LOCATION="yonge-and-bay"
OUT_DIR="oldto-screenshots"

mkdir -p $OUT_DIR

for EPS in $(seq 0.0001 0.00001 0.0002);
do
  echo "run for epsilon: $EPS"
  python oldtoronto/cluster_geojson.py --output_file data/clustered.images.geojson --epsilon $EPS
  python oldtoronto/gtjson_to_site.py data/clustered.images.geojson oldto-site/
  cd oldto-site
  yarn webpack
  cd -
  OUTPUT_PATH="${OUT_DIR}/${LOCATION}-clustered-${EPS}.png"
  echo $OUTPUT_PATH
  node scripts/old-to-screenshot.js $OUTPUT_PATH
done
