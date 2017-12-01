#!/usr/bin/env python3
"""Extract noun phrases from image titles.

These are consecutive sequences of capitalized words, e.g.
"Yonge Street" in "Photo at Yonge Street" (the first word is always capitalized).

Usage:

    ./extract_noun_phrases.py (streets|pois) (cutoff)

This prints a histogram of either street names or other points of interest (POIs) that
occur greater than (cutoff) times in the corpus of digitized photos.

The output is TSV for easy copy/pasting into a spreadsheet.
"""
import argparse
import json
import re
from collections import defaultdict, Counter

from weightreservoir import reservoir


def get_all_titles(images_ndjson):
    """Load a list of all titles from images.ndjson."""
    titles = []
    with open(images_ndjson) as f:
        for line in f:
            row = json.loads(line)
            title = row.get('title')
            if title:
                titles.append(title)
    return titles


noun_pat = re.compile(r'\b(?:[A-Z][A-Za-z.\']* ?)+')


def has_multiple_caps(noun):
    """Does a noun phrase contain multiple capital letters?"""
    return re.match(r'[A-Z].*[A-Z]', noun)


def extract_nouns(title):
    """Extract a list of capitalized noun phrases from a title string."""
    nouns = []
    for match in noun_pat.finditer(title):
        term = match.group()
        if match.start() == 0 and not has_multiple_caps(term):
            continue  # skip leading capitalized words that aren't part of a longer phrase.
        nouns.append(term.strip())
    return nouns


# Regex to determine if a string is a street name, e.g. "Yonge Street".
# Usually this is based on having "Street" in the name, but we also include a few
# special cases like "The Esplanade"
is_street_pat = re.compile(
    r'''\b(
        Street|St\.?|
        Avenue|Ave\.?|
        Road|Rd\.?|
        Drive|Dr.\?|
        Boulevard|Blvd\.?|
        Parkway|Pkwy.?|
        Highway|Hwy.?|
        Court|Crescent|Ct.?|
        Lane|
        Place|
        Terrace|
        Esplanade|
        Expressway)
        (?:\ (?:      # match a suffix, e.g. "Eglinton Avenue East"
            East|West|North|South|
            (?:E|W|N|S)\.?|  # either "E" or "E."
            Extension)
        )?$
    ''', re.X)

# Exclude some problematic noun phrases
STREET_BLACKLIST = {
    'Street North',
    'Street West',
    'Avenue West',
    "Eaton's College Street",
    "Eaton's Queen Street"
}
# Some unusually-named streets
STREET_WHITELIST = {
    'Ridge Drive Park',
    'Indian Grove',
    'Lake Front',
    'Lake Promenade',
    'Yarmouth Gardens',
    # To add:
    # 'Ashton Manor',
    # 'High Park Gardens'
}


def is_street(noun):
    """Returns whether the noun is a street name, e.g. "Yonge Street"."""
    if noun in STREET_WHITELIST:
        return True
    if noun in STREET_BLACKLIST:
        return False
    return is_street_pat.search(noun) is not None


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='extract pois or streets from images.ndjson and'
                                     'print to stdout')
    parser.add_argument('--noun_type', type=str,
                        help='pois|streets,  what type of noun to extract')
    parser.add_argument('--cutoff', type=int, default=1)
    parser.add_argument('--input', type=str, default='data/images.ndjson',
                        help='path to images.ndjson file to extract from')

    args = parser.parse_args()
    assert args.noun_type in ['pois', 'streets']
    want_streets = args.noun_type == 'streets'

    counts = Counter()
    examples = defaultdict(lambda: reservoir.UniformSampling(size=5))
    titles = get_all_titles(args.input)
    for title in titles:
        nouns = extract_nouns(title)
        for noun in nouns:
            if not has_multiple_caps(noun):
                continue  # Single words tend to be uninteresting.

            if is_street(noun) == want_streets:
                counts[noun] += 1
                examples[noun].addOne(title)

    print('Count\tName\tExample1\tExample2\tExample3\tExample4\tExample5')
    for k, v in counts.most_common():
        if v < args.cutoff:
            break
        examples_tsv = '\t'.join(examples[k].get())
        print('%d\t%s\t%s' % (v, k, examples_tsv))
