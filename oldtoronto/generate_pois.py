#!/usr/bin/env python3
"""Generate a list of place names and associated lat/lngs for geocoding.

This takes the list of noun phrases (noun-phrase-pois.txt) and attempts to attach OSM features to
them. It does this using a few strategies:

    - Match either the "name" or "wiki" tag in an OSM feature, subject to a few tweaks:
        - Removing "Toronto" ("Toronto City Hall" → "City Hall")
        - Parenthesized phrases, at a penalty ("Union Station (TTC)" → "Union Station")
    - For each name, rank the results according to some criteria:
        - Having a tag in our whitelist gives you bonus points.
        - Having an associated Wikipedia article gives you points.
    - Blacklisting a few terms that are known to be problematic.

The resulting list goes in toronto-pois.osm.csv. It's ~500-600 terms, short enough to be
verified by hand.

To update, grab an Ontario OSM extract and run:

    osmconvert ontario-latest.osm.pbf \
      -b=-79.697136,43.449277,-78.921914,43.990687 \
      --all-to-nodes \
      --add-bbox-tags \
      -o=toronto.osm
    osmfilter toronto.osm \
      --drop-author \
      --drop-version \
      --keep-tags='all name= old_name= loc_name= building= leisure= subway= wikipedia= amenity= tourism= place= highway= area= bBox=' \  # noqa
      --keep='name=' \
      -o=toronto+names.osm
    ./extract_noun_phrases.py pois 1 > noun-phrase-pois.txt
    ./generate_pois.py
"""

import csv
import itertools
import re

import untangle

# Prioritize features with these tags, e.g. "leisure=park".
GOOD_TAGS = {
    'leisure': {
        'park',
        'stadium',
        'playground'
    },
    'subway': set('yes'),
    'place': {
        'islet',
        'island'
    },
    'tourism': {
        'museum',
        'zoo',
        'hotel',
        'old_hotel',
        'attraction',
        'artwork',
        'gallery',
        'theme_park'
    },
    'building': set('yes'),
    'amenity': {
        'building',
        'place_of_worship',
        'library',
        'university',
        'school',
        'townhall',
        'charity',
        'marketplace',
    }
}

# Low value = non-specific
TAG_SCORES = {
    'leisure': 3,
    'subway': 2,
    'place': 1,
    'tourism': 4,
    'building': 5,
    'amenity': 6
}

# This list was made by hand by looking at terms which matched image titles.
BLACKLIST = set(open('data/poi-blacklist.txt').read().splitlines())


OUTPUT_FILE = 'data/toronto-pois.osm.csv'

root = untangle.parse('toronto+names.osm')


def strip_parens(name):
    return re.sub(r' \(.*\)', '', name)


def untorontoify(term):
    """Return a version of the term with "Toronto" removed.

    Useful if the name in OSM is something like "Union Square (Toronto)"
    or "Toronto City Hall".
    """
    return re.sub(r'^Toronto ', '', re.sub(r' \(Toronto\)', '', term))


blacklist_places = set()  # additional features to blacklist, found in data.
features = []
for el in root.osm.node:
    osm_id = el['id']
    lat = el['lat']
    lng = el['lon']

    tags = {}
    score = 0
    for node in el.children:
        k = node['k']
        v = node['v']
        tags[k] = v
    name = tags.get('name')
    if not name:
        continue

    for k, v in tags.items():
        values = GOOD_TAGS.get(k)
        if not values:
            continue

        if v in values:
            score = max(score, 10 * TAG_SCORES[k])
        else:
            score = max(score, TAG_SCORES[k])

    if name.lower() in BLACKLIST:
        continue

    names = [x for x in [name, tags.get('loc_name', tags.get('old_name'))] if x]

    wiki = tags.get('wikipedia', '')
    if wiki:
        score += 1  # A wiki link is a sign that this feature is important.

    if wiki and wiki[:3] == 'en:':
        names.append(wiki[3:])  # grab another name from the Wikipedia article

    if wiki == 'en:Exhibition Place':
        # This monkey patch gets us ~800 additional geocodes.
        names += ['CNE', 'C. N. E.', 'C.N.E.', 'Canadian National Exhibition']

    # These are large, non-specific areas.
    if tags.get('place') in {'suburb', 'neighbourhood', 'town'}:
        blacklist_places.add(name)

    # Roads should be handled via addresses or cross streets.
    # But sometimes squares are labeled as "highway=pedestrian", e.g. Nathan Phillips Square.
    if tags.get('highway') and not tags.get('area') == 'yes':
        continue

    # Try removing "Toronto" from our set of names.
    names = set(names + [untorontoify(n) for n in names])

    for name in names:
        if (len(name) > 4 and re.match(r'^[-A-Za-z .]+$', name)) or name == 'CNE':
            features.append((name, osm_id, lat, lng, score, tags['name'], wiki))

            # Try removing parenthesies, at a 50% score penalty.
            # This keeps "Berczy Park" outranking "Berczy (Wycliffe) Park"
            no_parens_name = strip_parens(name)
            if no_parens_name != name:
                features.append((
                    no_parens_name, osm_id, lat, lng, 0.5 * score, tags['name'], wiki))

# Read in the list of noun phrases.
noun_freq = {}
for row in csv.DictReader(open('data/noun-phrase-pois.txt'), delimiter='\t'):
    noun_freq[row['Name']] = int(row['Count'])


with open(OUTPUT_FILE, 'w') as f:
    out = csv.writer(f)
    out.writerow(['freq', 'name', 'osmid', 'lat', 'lng', 'score', 'OSM Name', 'Wiki'])

    # Group by name, order by rank and take the max.
    unique_features = [
        [str(noun_freq[name])] + list(max(it, key=lambda f: f[4]))
        for name, it in itertools.groupby(
            sorted(features, key=lambda f: (f[0], -f[4])), key=lambda f: f[0])
        if name in noun_freq and name not in blacklist_places and not name.lower() in BLACKLIST
    ]
    print('Found %d unique terms' % len(unique_features))
    out.writerows(unique_features)
