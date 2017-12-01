# Old Toronto

In order to create the visual experience OldTO, information from the
[Toronto Archives][1] gets translated
into a [GeoJSON][GeoJSON] formatted file. This is done via a series
of scripts and the [Google Maps Geocoding API][API] to use metadata
from the digital archives in order to predict where an individual image
was originally taken. The prediction uses regular expressions, a
natural language processing tool used here to extract geographic
information, and geocoding, the matching of geographic information to
a location on the earth's surface in the form of a position in a
geographic coordinate system.


* Live site: https://oldtoronto.sidewalklabs.com

## Development setup

In addition to the below steps, you will need to acquire a
Google Maps API Key. [Instructions here][api key]

    brew install coreutils csvkit
    # Require branch names to have "AP-" in them.
    cp ensure-branch-name.sh .git/hooks/pre-push
    pip install -r requirements.txt

## Building an OldNYC-style site

The OldTO site lives in `oldto-site`. In order to build it, set
the enviroment variable GMAPS_API_KEY to your own api key. Webpack
needs it to build the site when you run 'yarn webpack'. You can
spin it up by running it locally using http-server (install with
npm install -g http-server). Use the `--proxy` parameter to
specify the API server to use, for example to one on staging:

    cd oldto-site
    yarn
    yarn webpack
    cd oldto-site/dist
    http-server --proxy=https://api-staging.sidewalklabs.com

To iterate on the JavaScript, run:

    yarn watch &
    cd oldto-site/dist
    http-server --proxy=https://api-staging.sidewalklabs.com

To locally update the site, generate new geocodes (instructions below)
and then add the resulting .geojson file to the api server.

## Generating new geocodes

Add your google maps api key to the file oldtoronto/settings.py

### Update street names

To update the list of street names, run:

    oldtoronto/extract_noun_phrases.py streets 1 > /tmp/streets+examples.txt && \
    cut -f2 /tmp/streets+examples.txt | sed 1d | sort > data/streets.txt


### Generate the .geojson file

#### Individual Level Geocodes

To update the geocodes of individual images run:

    oldtoronto/geocode.py

#### Search the parent level metadata for geocodes
Some metadata that we want to associate with individual images is stored at the fonds or series
level. The process to update the series data should be run after the geocoding of the images
at the individual level.

    oldtoronto/geocode.py --input data/series.ndjson --output data/series-geocoded.json --strict true
    oldtoronto/mine_parents_for_data.py

#### Generate Geojson

In order to generate the geojson file that provides the location of the images using
individual level and parent level geocoding, run:

    oldtoronto/generate_geojson.py

#### Cluster Geojson

The geojson created by the geocoding results in images overlapping when presented on a map. In
order to clean this up, we can cluster images geographically close to one another.

    oldtoronto/cluster_geojson.py

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

If you want to understand the differences between two images.geojson file, you can
use the diff_geojson.py script. This file will create a series of .geojson files
showing differences between an A and B geojson. This is useful for using with the
data collected to the corrections google forms. Use those along with the
check_changes_using_* scripts.

Once you're ready to send the PR, run a diff on the full geocodes.


#### Using the makefile
In order to run the steps above and create a geojson file based on images.ndjson:

	make

## Histogram of Dates

After creating the images.ndjson file, there is a script and html file that will count the photos and group them by decade. If the file by-decade.json is already present then this is an unnecessary task.

    python date-distribution.py

The file by-decade-histogram.html will now display a histogram of the dates by decade.


[1]: https://www.toronto.ca/city-government/accountability-operations-customer-service/access-city-information-or-records/city-of-toronto-archives/
[m]: https://gencat.eloquent-systems.com/city-of-toronto-archives-m-public.html
[API]: https://developers.google.com/maps/documentation/geocoding/intro
[api key]: https://developers.google.com/maps/documentation/javascript/get-api-key
[image]: https://gencat.eloquent-systems.com/city-of-toronto-archives-m-permalink.html?key=571480
[file]: https://gencat.eloquent-systems.com/city-of-toronto-archives-m-permalink.html?key=348714
[GeoJSON]: http://geojson.org
