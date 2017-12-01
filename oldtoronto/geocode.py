#!/usr/bin/env python3
"""Runs through images.ndjson and uses the google maps geocoding api to find location for photos.
"""
import argparse
import csv
import functools
import json
import logging
import re
import sys

import googlemaps
import tqdm

from extract_noun_phrases import noun_pat
from fetcher import CacheSession
from logging_configuration import configure_logging
from settings import GMAPS_API_KEY
from utils import generators
from utils.id_sample import should_sample

googlemaps.client.requests.Session = googlemaps.client.requests.sessions.Session = CacheSession

GOOGLE = 'google'
EXACT = 'exact'

LOG = logging.getLogger(__name__)


def get_title(row):
    title = row.get('title', '').strip()
    if len(title) > 0:
        return title
    else:
        return None


# Replacement patterns for are_streets_same
_NORM_REPLACEMENTS = [
    (re.compile(r'Ave(nue)?', re.I), 'Av'),
    (re.compile(r'Street', re.I), 'St'),
    (re.compile(r'East', re.I), 'E'),
    (re.compile(r'North', re.I), 'N'),
    (re.compile(r'South', re.I), 'S'),
    (re.compile(r'West', re.I), 'W'),
    (re.compile(r'[^a-z ]', re.I), '')
]


def are_streets_same(street1, street2):
    """Are these two streets the same, accounting for St. vs. Street, etc."""
    def normalize(street):
        for pat, repl in _NORM_REPLACEMENTS:
            street = re.sub(pat, repl, street)
        return street
    a, b = (normalize(street) for street in (street1, street2))
    return a == b


def unique_streets(street_list):
    """Return a sublist with the unique streets, according to are_streets_same."""
    if len(street_list) > 10:  # avoid accidental N^2 with large inputs.
        return []
    if len(street_list) < 2:
        return street_list
    ok_list = [street_list[0]]
    for street in street_list[1:]:
        is_ok = True
        for other in ok_list:
            if are_streets_same(street, other):
                is_ok = False
                break
        if is_ok:
            ok_list.append(street)
    return ok_list


def exact_address_regex(street_re_str):
    decimal_suffix = '(?:(?:\.5)?)'
    exact_address_re_str = f'.*?(\d+{decimal_suffix})\s+(?:1/2\s)?({street_re_str})'
    return re.compile(exact_address_re_str)


def build_is_a_toronto_street_regex_str(street_list):
    # TODO: don't lower() the street names. case is significant!
    # We order streets from longest to shortest so that we get the most-specific match,
    # e.g. "King Street West" instead of "King Street".
    return '|'.join([
        s.strip().lower().replace('.', '\\.')
        for s in sorted(street_list, key=lambda street: -len(street))
        if s
    ])


def standalone_street_regex(street_re_str):
    return re.compile(rf'(?:^|[^a-z])({street_re_str})(?:[^a-z]|$)', re.I)


def build_place_name_regex(csv_file):
    name_to_place = {}
    with open(csv_file) as f:
        reader = csv.DictReader(f)
        for row in reader:
            # We lowercase names to get case-insensitive keys in the name_to_place dict.
            name = row['name'].lower()
            name_to_place[name] = row

    safe_names = [
        name.replace('.', r'\.')
        for name in name_to_place.keys()
        if (len(name) >= 5 or name == 'cne') and
        re.match(r'^[-A-Za-z .]+$', name)
    ]
    LOG.debug('Found %d safe names' % len(safe_names))
    regex = r'(?:^|[^a-z])(%s)(?:[^a-z]|$)' % '|'.join(safe_names)
    LOG.debug('POI regex: %s' % regex)
    return (re.compile(regex, flags=re.I), name_to_place)


CAPITALIZED_TOKEN = '(?:[A-Z][A-Za-z.\']*\s?)'
CAPITALIZED_TOKENS = f'{CAPITALIZED_TOKEN}+'
CARDINAL_DIRECTIONS = '(?:east|west|north|south)'
DIRECTION_FROM_RE = re.compile(rf'''
                                 .*?
                                 ({CAPITALIZED_TOKENS}),?
                                 (?:\s\[\?\])?             # remove lonely cruft
                                 (?:\s\:)?                 # remove more cruft
                                 \s
                                 (?:looking\s)?
                                 {CARDINAL_DIRECTIONS}
                                 \s(?:from|of|across|to)\s
                                 .*?
                                 ({CAPITALIZED_TOKENS})''', re.X)
JOINED_BY_AND_RE = re.compile(rf'''
                   .*?
                   ({CAPITALIZED_TOKENS}),?\s(?:and|&)\s({CAPITALIZED_TOKENS})
                   ''', re.X)

N_START = '(?:(?:^N)|\sn)'
S_START = '(?:(?:^S)|\ss)'
INTERCARDINAL_RE = rf'''(?:
                       {N_START}orth-?east|
                       {N_START}\.\s?e\.|
                       NE|
                       {N_START}orth-?west|
                       {N_START}\.\s?w\.|
                       NW|
                       {S_START}outh-?west|
                       {S_START}\.\s?w\.|
                       SW|
                       {S_START}outh-?east|
                       {S_START}\.\s?e\.|
                       SE)'''
OF_X_AND_Y = rf'''
                  (?:\sof)?\s
                  .*?
                  ({CAPITALIZED_TOKENS})
                  \sand\s
                  ({CAPITALIZED_TOKENS})
                  '''
PARSE_CORNER_OF_X_AND_Y_RE = re.compile(rf'''
                               .*?
                               {INTERCARDINAL_RE}
                               \scorner
                               (?:{OF_X_AND_Y})''', re.X)

SPLIT_ON_CORNER_RE = re.compile(rf'''
                               (.*?)
                               {INTERCARDINAL_RE}
                               \scorner
                               (.*)
                               ''', re.X)

X_AT_Y_RE = re.compile(rf'''
                       .*?
                       ({CAPITALIZED_TOKENS})
                       ,?\sat\s
                       ({CAPITALIZED_TOKENS})
                       .*?
                       {INTERCARDINAL_RE}\scorner
                       ''', re.X)

CORNER_OF_X_AND_Y = re.compile(rf'''
                               .*?
                               (?:c|^C)orner\sof\s
                               ({CAPITALIZED_TOKENS}),?
                               \sand\s
                               (?:the\s)?     # the Gardiner Expressway
                               ({CAPITALIZED_TOKENS}),?
                               ''', re.X)


# These are expected values for the "types" field of a result from Google Maps.
# If we search for cross streets and get an address back, it's almost certainly because
# these streets do not cross.
INTERSECTION_TYPE = {'intersection'}
ADDRESS_TYPE = {'street_address', 'premise'}


def parse_corner(title):
    m = PARSE_CORNER_OF_X_AND_Y_RE.match(title)
    if m:
        parse_capture = ('parse_corner', m.group(1).strip(), m.group(2).strip())
        search_term = f'{parse_capture[1]} and {parse_capture[2]} ontario toronto canada'
        return (GOOGLE, search_term, parse_capture, INTERSECTION_TYPE)
    m = SPLIT_ON_CORNER_RE.match(title)
    if m:
        first_street = None
        first_fragment = m.group(1).strip()
        caps = noun_pat.findall(first_fragment)
        if caps:
            first_street = caps[-1]  # get the street closest to corner fragment
            second_fragment = m.group(2).strip()
            caps = noun_pat.findall(second_fragment)
            if caps:
                second_street = caps[0]  # get the street closest to corner fragment
                parse_capture = ('parse_corner', first_street, second_street)
                search_term = f'{first_street} and {second_street} ontario toronto canada'
                return (GOOGLE, search_term, parse_capture, INTERSECTION_TYPE)
    m = X_AT_Y_RE.match(title)  # Spadina, at Yonge, southeast corner
    if m:
        parse_capture = ('parse_corner', m.group(1).strip(), m.group(2).strip())
        search_term = f'{parse_capture[1]} and {parse_capture[2]} ontario toronto canada'
        return (GOOGLE, search_term, parse_capture, INTERSECTION_TYPE)
    m = CORNER_OF_X_AND_Y.match(title)
    if m:
        parse_capture = ('parse_corner', m.group(1).strip(), m.group(2).strip())
        search_term = f'{parse_capture[1]} and {parse_capture[2]} ontario toronto canada'
        return (GOOGLE, search_term, parse_capture, INTERSECTION_TYPE)
    return None


def parse_direction_from(title):
    if title.startswith('Looking'):
        # otherwise we match things like "Looking at Spadina east over Bay" as (Looking, Spadina)
        title = title.strip('Looking')
    m = DIRECTION_FROM_RE.match(title)
    if m:
        street1 = m.group(1).strip()
        street2 = m.group(2).strip()
        search_results = ('looking', street1, street2)
        search_term = f'{street1} and {street2} ontario toronto canada'
        LOG.debug(f'parse_direction_from_pattern|search_term:{search_term}|title:{title}')
        return (GOOGLE, search_term, search_results, INTERSECTION_TYPE)
    return None


def parse_exact_address(regex, title):
    m = regex.match(title.lower())
    if m:
        search_term = f'{m.group(1)} {m.group(2)} ontario toronto canada'
        LOG.debug(f'parse_exact_address|search_term:{search_term}|title:{title}')
        return (GOOGLE, search_term, ('exact_address', m.group(1), m.group(2)), ADDRESS_TYPE)
    return None


def parse_streets_joined_by_and(title):
    m = JOINED_BY_AND_RE.match(title)
    if m:
        street1, street2 = m.group(1).strip(), m.group(2).strip()
        parse_results = ('streets_joined_by_and', street1, street2)
        search_term = f'{street1} and {street2} ontario toronto canada'
        LOG.debug(f'parse_streets_joined_by_and|search_term:{search_term}|title:{title}')
        return (GOOGLE,
                search_term,
                parse_results,
                INTERSECTION_TYPE)
    return None


def parse_two_streets(standalone_street_re, title):
    """Extract two street names if two are found in a title

    Returns:
        Either a search term for the geocoder or None.
    """
    all_matches = standalone_street_re.findall(title)
    matches = unique_streets(all_matches)
    if len(all_matches) < len(matches):
        LOG.debug(f'Removed duplicate streets: {all_matches} --> {matches}')
    if len(matches) < 2:
        return None
    if len(matches) > 2:
        LOG.debug(f'matched 3+ streets: {matches}; using first two.')

    street1, street2 = matches[:2]
    search_term = f'{street1} and {street2} ontario toronto canada'
    LOG.debug(f'parse_two_streets|search_term:{search_term}|title:{title}')
    return (GOOGLE, search_term, ('two streets', street1, street2), INTERSECTION_TYPE)


def parse_place_name(regex, place_map, title):
    matches = regex.findall(title)
    if not matches:
        return None
    name = max(matches, key=lambda name: place_map[name.lower()]['score']).lower()
    row = place_map[name]
    osmid = row['osmid']
    latlng = (row['lat'], row['lng'])
    LOG.debug('POI match %s (%s): %s' % (name, osmid, title))
    return (EXACT, name, latlng, '')


def get_search_term_from_title(parsers, title):
    return functools.reduce(lambda acc, curr: acc if acc else curr(title), parsers, None)


def call_geocoding_api(maps_client, search_string, expected_types):
    if maps_client is None:
        return fake_geocode(search_string)
    try:
        geocode_results = maps_client.geocode(search_string)
    except Exception as e:
        LOG.error(f'call_geocoding_api|search_term:{search_string}|error:{e}')
        LOG.exception(e)
        return None
    if geocode_results:
        if len(geocode_results) > 1:
            LOG.debug(f'Multiple geocode results for f{search_string}')
        geocode_result = geocode_results[0]

        types = set(geocode_result['types'])
        if len(types.intersection(expected_types)) == 0:
            LOG.debug(
                f'Discarding "{search_string}"; expected one of {expected_types}, got {types}')
            return None

        return {
            'lat': geocode_result['geometry']['location']['lat'],
            'lng': geocode_result['geometry']['location']['lng'],
            'address': geocode_result['formatted_address'],
            'place_id': geocode_result['place_id'],
            'types': geocode_result['types'],
            'accuracy': geocode_result['geometry']['location_type'],
            'search_term': search_string
        }
    LOG.debug(f'geocode_api_failure::{search_string}')
    return None


def fake_geocode(search_string):
    return {
        'lat': 43.647178,
        'lng': -79.359089,
        'address': search_string,
        'place_id': 'na',
        'accuracy': 'ROOFTOP',
        'types': ['street_address'],
        'search_term': search_string
    }


def write_result_to_file(filename, result):
    with open(filename, 'w') as f:
        f.write(json.dumps(result))


def geocode_title(parsers, maps_client, title, *, strict):
    outcome = get_search_term_from_title(parsers, title)
    if not outcome:
        return None
    technique, search_term, additional, expected_type = outcome
    if technique == GOOGLE:
        api_result = call_geocoding_api(maps_client, search_term, expected_type)
        if api_result is not None:
            if not strict or api_result['accuracy'] == 'ROOFTOP':
                return dict(api_result, **{
                    'original_title': title,
                    'technique': additional
                })
    elif technique == EXACT:
        if not strict or len(search_term) / len(title) > 0.85:
            lat, lng = additional
            return {
                'original_title': title,
                'lat': float(lat),
                'lng': float(lng),
                'search_term': search_term.lower(),
                'technique': ('POI', search_term)
            }
    return None


def row_to_result(parsers, maps_client, row, *, strict):
    title = get_title(row)
    if title is None:
        return None
    geocode_result = geocode_title(parsers, maps_client, title, strict=strict)
    if geocode_result:
        return row['uniqueID'], geocode_result
    else:
        return None


def main(input_file, street_names_file, pois_file, output_file, sampling_rate, ids,
         maps_client, strict):
    street_names = open(street_names_file).read().split('\n')
    toronto_street_re_str = build_is_a_toronto_street_regex_str(street_names)
    LOG.debug(f'Toronto street regex: {toronto_street_re_str}')
    exact_address_re = exact_address_regex(toronto_street_re_str)
    standalone_street_re = standalone_street_regex(toronto_street_re_str)
    place_name_re, place_map = build_place_name_regex(pois_file)

    parsers = [
        lambda x: parse_exact_address(exact_address_re, x),
        lambda x: parse_corner(x),
        lambda x: parse_direction_from(x),
        lambda x: parse_two_streets(standalone_street_re, x),
        lambda x: parse_streets_joined_by_and(x),
        lambda x: parse_place_name(place_name_re, place_map, x)
    ]

    results = {}
    # note: we convert to a list to get a nicer progress bar.
    for row in tqdm.tqdm(list(generators.read_ndjson_file(input_file))):
        id_ = row['uniqueID']
        if ids is not None and id_ not in ids:
            continue

        if not should_sample(id_, sampling_rate):
            LOG.debug(f'Skipping {id_} due to sampling rate')
            continue

        geocode_result = row_to_result(parsers, maps_client, row, strict=strict)
        if geocode_result is not None:
            uid, result = geocode_result
            results[uid] = result
        LOG.debug(f'{id_}: {geocode_result}')
    write_result_to_file(output_file, results)


if __name__ == '__main__':
    parser = argparse.ArgumentParser('Geocode texts using a variety of approaches.')
    parser.add_argument('--input', type=str,
                        help='ndjson formatted file containing the items to be geocoded',
                        default='data/images.ndjson')
    parser.add_argument('--street_names', type=str,
                        help='text file containing street names',
                        default='data/streets.txt')
    parser.add_argument('--pois', type=str,
                        help='csv containing pois extracted from osm',
                        default='data/toronto-pois.osm.csv')
    parser.add_argument('--output', type=str,
                        help='json encoded output file with the geocoded results',
                        default='data/geocode_results.json')
    parser.add_argument('--logfile', type=str,
                        help='file to log to',
                        default=__file__ + '.log')
    parser.add_argument('--strict', type=bool,
                        help='if set, use only the most exact matches: require ROOFTOP accuracy '
                             'for Google geocoding or almost complete overlap for poi name '
                             'matching',
                        default=False)
    parser.add_argument('--no_network',
                        help='If set, stub out the Google Maps API and avoid the network. '
                        'Useful for isolating changes to parsing.',
                        action='store_true')
    parser.add_argument('--sample', type=float,
                        help='Process a deterministic sample of images. 1=100%%, 0.1=10%%, etc.',
                        default=1.0)
    parser.add_argument('--ids', type=str,
                        help='Comma-separated list of uniqueIDs to process. Useful for debugging.',
                        default='')
    args = parser.parse_args()

    configure_logging(args.logfile)

    ids = args.ids.split(',') if args.ids else None

    if args.no_network:
        sys.stderr.write('USING FAKE MAPS CLIENT!!\n')
        gmaps_client = None
    else:
        gmaps_client = googlemaps.Client(key=GMAPS_API_KEY)
    main(args.input, args.street_names, args.pois, args.output, args.sample, ids,
         gmaps_client, args.strict)
