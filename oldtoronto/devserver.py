#!/usr/bin/env python
"""Run a dev server for the OldTO API.

This is useful for iterating on geocoding since it will reload the GeoJSON file if it changes.

Supported endpoints:
- /api/oldtoronto/lat_lng_counts?var=lat_lons
- /api/oldtoronto/by_location?lat=43.651501&lng=-79.359842
- /api/layer/oldtoronto/86514
"""

import argparse
from collections import defaultdict, Counter
import copy
import json
import os

from flask import Flask, abort, jsonify, request, Response
from haversine import haversine

geojson_file = None  # filled in in __main__
mtime = 0  # last modified time
features = []


def old_toronto_key(lat, lng):
    """"Return a key for a record that matches the old toronto convention of the
    concatenation of the lat and lng rounded to 6 decimals.
    Rounding is done differently in JavaScript from Python - 3.499999 rounds to
    3.4 in Python, 3.5 in JavaScript, hence the workaround to first round to 7
    decimals and then to 6.
    """
    def round6(f):
        return round(round(f, 7), 6)

    lat = round6(lat)
    lng = round6(lng)

    return f'{lat:2.6f},{lng:2.6f}'


app = Flask(__name__)


# Check for changes to the GeoJSON file before every request.
@app.before_request
def maybe_load_features():
    global features, mtime
    new_mtime = os.stat(geojson_file).st_mtime
    if new_mtime > mtime:
        mtime = new_mtime
        # Filter out the null geometries ahead of time.
        features = [
            f
            for f in json.load(open(args.geojson))['features']
            if f['geometry']
        ]
        print(f'Loaded {len(features)} features from {geojson_file}')


@app.route('/api/oldtoronto/lat_lng_counts')
def lat_lng_counts():
    counts = defaultdict(Counter)
    for f in features:
        lng, lat = f['geometry']['coordinates']
        year = f['properties']['date'] or ''
        counts[old_toronto_key(lat, lng)][year] += 1

    var = request.args.get('var')
    js = 'var %s=%s' % (var, json.dumps(counts))
    return Response(js, mimetype='text/javascript')


@app.route('/api/oldtoronto/by_location')
def by_location():
    def poi_to_rec(poi):
        props = copy.deepcopy(poi['properties'])
        image = props.pop('image')
        image['image_url'] = image.pop('url')
        return dict(image, id=poi['id'], **props)

    pt = (float(request.args.get('lat')), float(request.args.get('lng')))
    results = {
        f['id']: poi_to_rec(f)
        for f in features
        if haversine(pt, f['geometry']['coordinates'][::-1]) < 0.005
    }
    return jsonify(results)


@app.route('/api/layer/oldtoronto/<photo_id>')
def by_photo_id(photo_id):
    feature = [f for f in features if f['id'] == photo_id]
    if feature:
        return jsonify(feature[0])
    else:
        abort(404)


if __name__ == '__main__':
    parser = argparse.ArgumentParser('Run a simple API server for Old Toronto')
    parser.add_argument('--port', type=int, help='Port on which to serve.', default=8081)
    parser.add_argument('geojson', type=str, default='data/images.geojson',
                        help='Path to images.geojson')
    args = parser.parse_args()

    geojson_file = args.geojson
    maybe_load_features()

    app.run(host='0.0.0.0', port=args.port, debug=True)
