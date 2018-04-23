# OldTO

OldTO showcases historic photographs of Toronto by placing them on a map.
You can read more about the project on its [about page][about] or on the
[Sidewalk Labs Blog][blog].

## How it works

OldTO begins with data from the [Toronto Archives][1], which you can find
in [`data/images.ndjson`](/data/images.ndjson).

To place the images on a map ("geocode" them), we use a [list of Toronto
street names](/data/streets.txt) and a collection of [regular expressions][]
which look for addresses and cross-streets. We send these through the
[Google Maps Geocoding API][API] to get latitudes and longitudes for the
images. We also incorporate a [set of points of interest](/data/toronto-pois.osm.csv)
for popular locations like the CN Tower or City Hall.

* Live site: https://oldtoronto.sidewalklabs.com

## Development setup

Setup dependencies:

    brew install coreutils csvkit
    pip install -r requirements.txt

## Building an OldNYC-style site

The OldTO site lives in `oldto-site`. In order to build it, set
the enviroment variable `GMAPS_API_KEY` to your own api key:

    export GMAPS_API_KEY=...

See [instructions here][api key] for getting an API key.

Webpack needs this to build the site when you run 'yarn webpack'. You can
spin it up by running it locally using `http-server` (install with
`npm install -g http-server`).

    cd oldto-site
    yarn
    yarn webpack
    cd ../oldto-site/dist
    http-server --proxy=https://api.sidewalklabs.com

To iterate on the JavaScript, run:

    yarn watch &
    cd oldto-site/dist
    http-server --proxy=https://api.sidewalklabs.com

## Generating new geocodes

First, add your Google Maps API key to the file `oldtoronto/settings.py`.

Next, you'll first want to download cached geocodes from [here][cached-geocodes].
Unzip this file into `cache/maps.googleapis.com`. This will make the geocoding
pipeline run faster and more consistently than geocoding from scratch.

With this in place, you can update `images.geojson` by running:

    make

## Serving new geocodes

If you've generated new geocodes, you'll need to run your own API server to serve them.
You can do this by running:

    oldtoronto/devserver.py data/images.geojson &
    cd oldto-site/dist
    http-server --proxy=http://localhost:8081

If you've generated geocodes in a different location, change `data/images.geojson` to that.

#### Analyzing results and changes

Before sending out a PR with geocoding changes, you'll want to run a diff to evaluate the change.

For a quick check, you can operate on a 5% sample and diff that against `master`:

    oldtoronto/geocode.py --sample 0.05 --output /tmp/geocode_results.new.5pct.json
    oldtoronto/diff_geocodes.py --sample 0.05 /tmp/geocode_results.new.5pct.json

To calculate metrics using truth data (must have jq installed):

    grep -E  "$(jq '.features[] | .id' data/truth.gtjson | sed s/\"//g | paste -s -d '|' )" data/images.ndjson > data/test.images.ndjson
    oldtoronto/geocode.py --input data/test.images.ndjson
    oldtoronto/generate_geojson.py --geocode_results data/test.images.ndjson --output data/test.images.geojson
    oldtoronto/calculate_metrics.py --truth_data data/truth.gtjson --computed_data data/test.images.geojson

To debug a specific image ID, run something like:

    oldtoronto/geocode.py --ids 520805 --output /tmp/geocode.json && \
    cat oldtoronto/geocode.py.log | grep -v regex

If you want to understand the differences between two `images.geojson` files, you can
use the `diff_geojson.py` script. This file will create a series of `.geojson` files
showing differences between an A and B GeoJSON. This is useful for using with the
data collected to the corrections google forms. Use those along with the
`check_changes_using_*` scripts.

Once you're ready to send the PR, run a diff on the full geocodes.

### Update street names

To update the list of street names, run:

    oldtoronto/extract_noun_phrases.py streets 1 > /tmp/streets+examples.txt && \
    cut -f2 /tmp/streets+examples.txt | sed 1d | sort > data/streets.txt

[1]: https://www.toronto.ca/city-government/accountability-operations-customer-service/access-city-information-or-records/city-of-toronto-archives/
[m]: https://gencat.eloquent-systems.com/city-of-toronto-archives-m-public.html
[API]: https://developers.google.com/maps/documentation/geocoding/intro
[api key]: https://developers.google.com/maps/documentation/javascript/get-api-key
[image]: https://gencat.eloquent-systems.com/city-of-toronto-archives-m-permalink.html?key=571480
[file]: https://gencat.eloquent-systems.com/city-of-toronto-archives-m-permalink.html?key=348714
[GeoJSON]: http://geojson.org
[cached-geocodes]: https://drive.google.com/open?id=1F0J3RHUA1bVRJTJGlRKDuE_IVpb1BwQH
[about]: https://oldtoronto.sidewalklabs.com/about.html
[blog]: https://medium.com/sidewalk-talk/explore-toronto-through-historical-photos-one-block-at-a-time-2fbcd38b511a
