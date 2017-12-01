#!/usr/bin/env python3
"""Produce a JavaScript file with a mapping from lat/lng to IDs.

This is used for the geocode correction UI.
"""

import argparse
from collections import defaultdict
import json


def main(input_geojson, output_js):
    fc = json.load(open(input_geojson))

    ll_to_ids = defaultdict(list)
    for f in fc['features']:
        # Features with null geometries couldn't be geocoded and aren't shown on the site.
        if f['geometry'] is None:
            continue
        lng, lat = f['geometry']['coordinates']
        ll_to_ids['%.6f,%.6f' % (lat, lng)].append(int(f['id']))
    open(output_js, 'w').write('var ll_to_ids = ' + json.dumps(ll_to_ids, separators=(',', ':')))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        'Create a JavaScript file with all the image IDs to support ' +
        'the location correction tool.')
    parser.add_argument('input_geojson', help='Path to images.geojson file', type=str)
    parser.add_argument('output_js', help='Path to JavaScript output file', type=str,
                        default='oldto-site/corrections/ids.js', nargs='?')
    args = parser.parse_args()

    main(args.input_geojson, args.output_js)
