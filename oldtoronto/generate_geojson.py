#!/usr/bin/env python3
"""Collect data on all the images into a GeoTempoJSON file.

Inputs:
    data/images.ndjson
    data/geocode_results.json
    data/image-sizes.txt

Output:
    data/images.geojson
"""
import argparse
import json
import os
import pandas as pd

from date_distribution import parse_year
from toronto_archives import SHORT_URL_PATTERN
from utils.generators import read_ndjson_file


def load_image_sizes(sizes_file):
    """Load image sizes into a path --> [width, height] dict."""
    # The image sizes file is the output of something like
    # identify 'images/*.jpg' > image-sizes.txt
    # A sample line looks like:
    # images/f0124_fl0001_id0001.jpg JPEG 1050x715 1050x715+0+0 8-bit sRGB 122804B 0.000u 0:00.009
    path_to_dimensions = {}
    for line in open(sizes_file):
        parts = line.split(' ')
        path = os.path.basename(parts[0])
        dims = [int(x) for x in parts[2].split('x')]
        path_to_dimensions[path] = dims
    return path_to_dimensions


def get_thumbnail_url(image_url):
    base_url = 'https://storage.googleapis.com/sidewalk-old-toronto/thumbnails/'
    ext = 'jpg'

    filename = os.path.splitext(os.path.basename(image_url))[0]
    return os.path.join(base_url, '{}.{}'.format(filename, ext))


def get_mirror_url(image_url):
    base_url = 'https://storage.googleapis.com/sidewalk-old-toronto/images/'
    ext = 'jpg'

    filename = os.path.splitext(os.path.basename(image_url))[0]
    return os.path.join(base_url, '{}.{}'.format(filename, ext))


def load_patch_csv(patch_csv):
    """
    Load the patch csv as a dict. All photo's that have an explicit lat, lng
    value are returned. Photo's occuring more than once are returned with a value
    of None unless their Fixed column is set to the 'Yes' (case sensitive).

    Args:
        patch_csv: path or remote spec of the csv

    Returns:
        A dictionary keyed by photo id. If the value is None, skip this record;
        if it contains a tuple, use that as an override value for lat, lng
    """
    data = pd.read_csv(patch_csv, dtype={'Fixed': object})
    fixed = set(data[data['Fixed'] == 'Yes']['Photo Id'])
    photo_id_to_lat_lng = {}
    for _, row in data[pd.notnull(data['Lat']) & pd.notnull(data['Lng'])].iterrows():
        lat_lng = (row['Lat'], row['Lng'])
        photo_id = row['Photo Id']
        if photo_id_to_lat_lng.get(photo_id, lat_lng) != lat_lng:
            raise ValueError(f'Ambiguous fix for {photo_id}')
        photo_id_to_lat_lng[photo_id] = lat_lng
    photo_counts = data['Photo Id'].value_counts()
    occurs_often = set(photo_counts[photo_counts > 1].index)
    # Conctruct the return dict by checking for each in either photo_id_to_lat_lng or
    # occurs_often if they are in fixed and if not lookup their value:
    all_keys = occurs_often.union(photo_id_to_lat_lng.keys())
    return {str(key): photo_id_to_lat_lng.get(key) for key in all_keys if key not in fixed}


if __name__ == '__main__':
    parser = argparse.ArgumentParser('Collect data on all the images into a GeoTempoJSON file.')
    parser.add_argument('--parent_data', type=str,
                        help='mapping uniqueID to metadata scraped from parent series/fonds/etc',
                        default='data/parent_mined_data.json')
    parser.add_argument('--geocode_results', type=str,
                        help='json results from geocoding files',
                        default='data/geocode_results.json')
    parser.add_argument('--path_to_size', type=str,
                        help='txt file containing size in pixels of each images.',
                        default='data/image-sizes.txt')
    parser.add_argument('--output', type=str,
                        help='geojson encoded version of geocodes and images metadata',
                        default='data/images.geojson')
    parser.add_argument('--patch_csv', type=str,
                        help='path to a csv to override lat/lngs. Can be local or remote. '
                             'rows with missing lat/lngs will be skipped in the output.',
                        default='data/Old Toronto Responses - Override Sheet.csv')
    args = parser.parse_args()

    parent_data = json.load(open(args.parent_data))
    id_to_geocode = json.load(open(args.geocode_results))
    path_to_size = load_image_sizes(args.path_to_size)

    num_total = 0
    num_missing_ids = 0
    num_missing_images = 0
    num_processed = 0
    num_with_dates = 0
    num_with_geocodes = 0
    num_with_parent_geocodes = 0
    num_invalid = 0
    num_excluded_csv = 0

    patch_csv = load_patch_csv(args.patch_csv)

    features = []
    for record in read_ndjson_file('data/images.ndjson'):
        num_total += 1

        id_ = record.get('uniqueID')
        if not id_:
            num_missing_ids += 1
            continue

        if not record.get('imageLink'):
            num_missing_images += 1
            continue

        patched = patch_csv.get(id_, '')
        if patched is None:
            num_excluded_csv += 1
            continue

        parent_rec = parent_data.get(id_, {})
        num_processed += 1
        geocode = id_to_geocode.get(id_)

        if not geocode and 'lat' in parent_rec:
            geocode = parent_rec
            num_with_parent_geocodes += 1

        if geocode:
            num_with_geocodes += 1
            if patched:
                geocode['lat'], geocode['lng'] = patched

        year_range = parse_year(record.get('date', parent_rec.get('date', '')))
        year = None
        if year_range:
            num_with_dates += 1
            year = year_range[0] or year_range[1]  # TODO(danvk): represent the range itself.

        image_url = record.get('imageLink')
        assert image_url
        dims = path_to_size.get(os.path.basename(image_url))

        # If dims is none it means that ImageMagick was not able to parse the image so it doesn't
        # appear in our image dimension list. This could be because the image was corrupt, or did
        # not exist on the original website. Regardless, it can't be displayed.
        if dims is None:
            num_invalid += 1
            continue

        features.append({
            'id': id_,
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [geocode['lng'], geocode['lat']],
            } if geocode else None,
            'properties': {
                'title': record.get('title'),
                'date': str(year) if year else None,
                'url': SHORT_URL_PATTERN % id_,
                'geocode': geocode,
                'image': {
                    'url': get_mirror_url(image_url),
                    'width': dims[0],
                    'height': dims[1],
                    'thumb_url': get_thumbnail_url(image_url)
                },
                'archives_fields': {
                    k: record.get(k)
                    for k in ('date', 'physical_desc', 'citation', 'condition', 'scope')
                }
            }
        })

    print('   Total records: %s' % num_total)

    print('  .excluded by csv: %s' % num_excluded_csv)
    print('  ...invalid image: %s' % num_invalid)
    print('  .....missing IDs: %s' % num_missing_ids)
    print('  .......or images: %s' % num_missing_images)
    print('')
    print('   num processed: %s' % num_processed)
    print(' ...and geocodes: %s' % num_with_geocodes)
    print(' ...from parents: %s' % num_with_parent_geocodes)
    print('   ...with dates: %s' % num_with_dates)

    json.dump({
        'type': 'FeatureCollection',
        'features': features
    }, open(args.output, 'w'))
