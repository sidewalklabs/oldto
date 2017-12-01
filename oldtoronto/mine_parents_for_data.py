#!/usr/bin/env python3
"""Mine parents for missing data.

Not all images have geocodes or dates. However the series that they belong
to might. For dates this is straightforward and nets us almost 90k dates.

For geocodes we pursue two strategies. First we run the geocoder in strict mode
over the titles of the series. Any image in a series such geocoded is
presumed to have that geocode also. This will give us about a thousand geocodes.

The second strategy is to assign the geocode to any series that contains at least
two geocoded images with coordinates that are close to each other. This in turn
results in about 2000 geocodes.

Since there is overlap between the two strategies, we end up with about 2 500 extra
geocodes in total, or 660 new ones compared to what we already had. Only one overlaps
with our test set - toronto island. We mark it as too far, but danvk says it is
probably ok.

"""

import argparse
import json
from collections import defaultdict

import haversine
import tqdm

from utils.generators import read_ndjson_file

# Skip the urban design photographs, they are all over the place:
URBAN_DESIGN_PHOTOGRAPHS_ID = '306110'


def walk_up(id_to_series, item):
    parents = [parent for parent, _ in item.get('part_of_links', [])]
    if not parents:
        return []
    assert len(parents) == 1
    return parents + walk_up(id_to_series, id_to_series[parents[0]])


def build_series_to_lat_lng(*, images, geocoded, id_to_series, series_geocoded):
    """
    Build a dictionary from the id to a series to the estimated lat/lng of the
    series.

    Args:
        images: the image set
        geocoded: geocoding information for images
        id_to_series: dictionary from series id to serieis information
        series_geocoded: geocoded information for the series

    Returns:
        the mapping from series id to lat/lng.
    """
    lat_lng_candidates = defaultdict(list)
    for img in images:
        info = geocoded.get(img['uniqueID'])
        if info:
            for parent in walk_up(id_to_series, img):
                lat_lng_candidates[parent].append((info['lat'], info['lng']))
    print(f'found {len(lat_lng_candidates)} lat,lng candidates')

    parent_to_lat_lng = {}
    for parent, lst in lat_lng_candidates.items():
        info = id_to_series[parent]
        if any(p for p, _ in info.get('part_of_links', []) if p == URBAN_DESIGN_PHOTOGRAPHS_ID):
            continue
        parent_geocode = series_geocoded.get(parent)
        if parent_geocode:
            parent_to_lat_lng[parent] = (parent_geocode['lat'], parent_geocode['lng'])
        if len(lst) < 2:
            continue
        center_lat = sum(lat for lat, lng in lst) / len(lst)
        center_lng = sum(lng for lat, lng in lst) / len(lst)
        if all(haversine.haversine((center_lat, center_lng), p) < 0.01 for p in lst):
            parent_to_lat_lng[parent] = (center_lat, center_lng)
    print(f'found {len(parent_to_lat_lng)} parents with lat/lngs')
    return parent_to_lat_lng


def main(*, images, geocoded, id_to_series, series_geocoded, output_handle):
    series_to_lat_lng = build_series_to_lat_lng(images=images,
                                                geocoded=geocoded,
                                                id_to_series=id_to_series,
                                                series_geocoded=series_geocoded)

    alt_info = {}
    lat_lngs_found = 0
    dates_found = 0
    for img in tqdm.tqdm(images):
        lat_lng = None
        search_term = None
        date = None
        for parent in walk_up(id_to_series, img):
            title = id_to_series[parent]['title']
            # Skip records whose first word seems like a plural:
            if title.split(' ', 1)[0].endswith('s'):
                break
            if not lat_lng:
                lat_lng = series_to_lat_lng.get(parent)
                if lat_lng:
                    lat_lngs_found += 1
                    search_term = 'series:' + title
            if not date:
                date = id_to_series[parent].get('date')
                if date:
                    dates_found += 1
            if date and lat_lng:
                alt_info[img['uniqueID']] = {'lat': lat_lng[0],
                                             'lng': lat_lng[1],
                                             'search_term': search_term,
                                             'date': date}
                break

    print(f'found {lat_lngs_found} lat/lngs, {dates_found} dates')
    json.dump(alt_info, output_handle)


if __name__ == '__main__':
    parser = argparse.ArgumentParser('Mine parents for more data.')
    parser.add_argument('--series', type=str,
                        help='ndjson formatted file containing the series information',
                        default='data/series.ndjson')
    parser.add_argument('--geocoded_results', type=str,
                        help='json file with image-id -> geocode results',
                        default='data/geocode_results.json')
    parser.add_argument('--series_geocoded', type=str,
                        help='json file with series-id -> geocode results',
                        default='data/series-geocoded.json')
    parser.add_argument('--images', type=str,
                        help='ndjson formatted file containing all images',
                        default='data/images.ndjson')
    parser.add_argument('--output', type=str,
                        help='json file to write out the mined values keyed by image id',
                        default='data/parent_mined_data.json')
    args = parser.parse_args()

    images = [json.loads(s) for s in open(args.images)]
    geocoded = json.load(open(args.geocoded_results))
    id_to_series = {item['uniqueID']: item for item in read_ndjson_file(args.series)}
    series_geocoded = json.load(open(args.series_geocoded))

    print(f'read {len(id_to_series)} series,'
          f' {len(geocoded)} geocoded images'
          f' and {len(images)} images')

    with open(args.output, 'w') as fout:
        main(images=images,
             geocoded=geocoded,
             id_to_series=id_to_series,
             series_geocoded=series_geocoded,
             output_handle=fout)
