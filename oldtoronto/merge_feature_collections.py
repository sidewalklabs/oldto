#!/usr/bin/env python
"""Merge several GeoJSON feature collections into one.

Usage:

    merge_feature_collection.py in1.geojson in2.geojson out.geojson
"""

import json
import sys


if __name__ == '__main__':
    assert len(sys.argv) >= 3
    inputs = sys.argv[1:-1]
    output = sys.argv[-1]

    features = []
    for input_file in inputs:
        fc = json.load(open(input_file))
        assert fc['type'] == 'FeatureCollection'

        features += fc['features']

    with open(output, 'w') as out:
        json.dump({
            'type': 'FeatureCollection',
            'features': features
        }, out)
