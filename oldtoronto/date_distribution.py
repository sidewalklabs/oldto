#!/usr/bin/env python3
"""Parse the dates field from the images.ndjson, and then group by decade.

Usage:
    python date_distribution.py $log_filename
"""

from collections import defaultdict
import json
import logging
import re
import sys

from dateutil.parser import parse

from logging_configuration import configure_logging
from utils import generators


LOG = logging.getLogger(__name__)

INPUT_FILENAME = 'data/images.ndjson'
JSON_OUTPUT = 'data/by-decade.json'

# These regular expressions are applied in order to dates until none of them match.
# If any matches, the date is replaced with the first capture group.
CLEANER_RES = [
    re.compile('^(?:ca.|circa)\s*(.*)'),  # remove leading "ca", e.g. 'ca. June 1922'
    re.compile('^(.*)\?$'),  # remove trailing ?, e.g '1948-?'
    re.compile('^[\[(\{](.*)'),  # remove surrounding braces, e.g. '[1890]'
    re.compile('^(.*)[\]\}).]$'),  # remove surrounding braces, e.g. '[1890]'
    re.compile('^\s+(.*)'),  # leading whitespace
    re.compile('(.*)\s+$'),  # trailing whitespace
    re.compile(r'.*originally created (.*)'),
    # meaningful keywords that we just ignore for now.
    re.compile('^(?:spring|summer|fall|winter) (.*)')
]


def _year_range(m):
    """Helper function to construct a range of years from a regex."""
    return (m.group(1), m.group(2))


# Each of these gets a crack at parsing the date. If the regex matches, the lambda
# returns a (start_year, end_year) tuple for that pattern.
PARSERS = [
    (
        # e.g. '193-'; becomes '1930/1939'
        re.compile(r'^(\d\d\d)-?$'),
        lambda m: (m.group(1) + '0', m.group(1) + '9')
    ),
    (
        # e.g. 'between 1900 and 1910'
        re.compile(r'^be+t+we+n (\d{4})\??\s*(?:ana*d|or|-)\s*(\d{4})$'), _year_range
    ),
    (
        # e.g. '1945-1952', '1945 or 1946', '1940 to 1950'
        re.compile(r'^(\d{4})\s*(?:-|to|or)\s*(\d{4})$'), _year_range
    ),
    (
        # e.g. '1945-52'
        re.compile(r'^(\d{2})(\d{2})-(\d{2})$'),
        lambda m: (m.group(1) + m.group(2), m.group(1) + m.group(3))
    ),
    (
        # e.g. 'before 1900'
        re.compile(r'^before (\d{4})'),
        lambda m: (None, m.group(1))
    ),
    (
        # e.g. 'after 1900'
        re.compile(r'^after (\d{4})'),
        lambda m: (m.group(1), None)
    ),
    (
        # June 15-19, 1948
        re.compile(r'[A-z][a-z]+ \d\d\-\d\d, (\d{4})$'),
        lambda m: (m.group(1), m.group(1))
    ),
]


def is_valid_year(year):
    """Is the (integer) year in a plausible range of dates?"""
    return 1750 <= year <= 2019


def use_date_util_parser(date_string):
    try:
        date = parse(date_string)
        # dates looking like "193?" get parsed to 193
        if not is_valid_year(date.year):
            return None
        return (str(date.year), str(date.year))
    except (ValueError, OverflowError):
        return None


def parse_year(date_string):
    """Parse string and extract a range of years from date.

    Return:
        None if a year is not found in the string, otherwise the parsed date is returned as a
        (start_year, end_year) string tuple. If either is unknown, it will be None.
    """
    if len(date_string) == 0:
        return None

    date_string = date_string.lower()
    for cleaner_re in CLEANER_RES:
        m = cleaner_re.match(date_string)
        if m:
            return parse_year(m.group(1))

    for pattern, parser in PARSERS:
        m = pattern.match(date_string)
        if m:
            return parser(m)

    result = use_date_util_parser(date_string)
    if result:
        return result
    else:
        # If the whitelist of patterns fails, look for four digit numbers as a last resort.
        return _find_loose_date(date_string)


def _find_loose_date(date_string):
    """Look for four digit numbers in the string. If there's only one, return it."""
    if re.search(r'digit', date_string):
        # Might be something like "digitized 2010", which we want to avoid.
        return None
    # find all the (unique) four digit numbers in the date_string.
    matches = set(re.findall(r'\b\d{4}\b', date_string))
    if len(matches) != 1:
        return None
    year = list(matches)[0]
    if is_valid_year(int(year)):
        LOG.debug('Parsed %s from "%s" as a loose date.' % (year, date_string))
        return (year, year)


def get_parsed_date(row):
    """Returns either an int year or None for an image record."""
    input_years = row.get('date', '').strip()
    return parse_year(input_years)


def write_as_json_to_file(dictionary, filename):
    with open(filename, 'w') as f:
        json.dump(dictionary, f)


def main(input_filename, json_output):
    """Searches the images.ndjson file and counts the number of dates found per decade."""
    num_parsed = 0
    num_total = 0
    by_decade = defaultdict(int)
    for row in generators.read_ndjson_file(input_filename):
        ds = row.get('date')
        if not ds:
            continue
        num_total += 1
        d = get_parsed_date(row)
        if not d:
            LOG.debug('Unable to parse date for %10s: %s' % (row['uniqueID'], ds))
        else:
            num_parsed += 1
            year = int(d[0] or d[1])  # ignore the range for now.
            by_decade[year // 10] += 1

    LOG.info('Parsed %d/%d dates (%.2f%%)' % (
        num_parsed, num_total, 100.0 * num_parsed / num_total))
    counts_by_decade = [
        {
            'decade': '%d0' % decade,
            'count': by_decade[decade]
        } for decade in sorted(by_decade.keys())
    ]
    write_as_json_to_file(counts_by_decade, json_output)


if __name__ == '__main__':
    assert len(sys.argv) <= 2
    log_file = sys.argv[1] if len(sys.argv) == 2 else __file__ + '.log'
    configure_logging(log_file)
    main(INPUT_FILENAME, JSON_OUTPUT)
