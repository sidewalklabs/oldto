#!/usr/bin/env python3
"""Verify that we have data on all files, subseries, series, fonds, etc.

"""

import json
import sys

from toronto_archives import get_citation_hierarchy

INPUT_FILE = 'data/images.ndjson'
OUTPUT_FILE = 'data/images+parents.ndjson'


def load_series():
    """Returns a {citation: record} structure."""
    out = {}
    num_missing = 0
    parts_of = set()
    for line in open('data/series.ndjson'):
        record = json.loads(line)
        id_ = record['uniqueID']
        try:
            out[record['citation']] = record
        except KeyError:
            sys.stderr.write('Missing data for %s\n' % id_)
            num_missing += 1
        for link in record.get('part_of_links', []):
            parts_of.add(link[0])
    if num_missing > 0:
        sys.stderr.write('Missing data for %s files\n' % num_missing)
        with open('extra-ids.txt', 'w') as f:
            for part in parts_of:
                f.write('%s\n' % part)
    return out


def check_images(citation_to_series):
    missing = set()
    f = open(OUTPUT_FILE, 'w')
    for line in open(INPUT_FILE):
        record = json.loads(line)
        if len(record) == 0:
            continue
        citation = record.get('citations')
        if not citation:
            sys.stderr.write('Missing citation for %s\n' % record)
            continue

        parents = []
        for series in get_citation_hierarchy(citation):
            if series not in citation_to_series:
                print('Missing: "%s" from %s' % (series, record['uniqueID']))
                missing.add(series)
            else:
                parents.append(citation_to_series[series])
        record['parents'] = parents
        f.write(json.dumps(record) + '\n')
    print('Missing %d series' % len(missing))
    for series in missing:
        print('  %s' % series)


if __name__ == '__main__':
    citation_to_series = {k: v['uniqueID'] for k, v in load_series().items()}
    check_images(citation_to_series)
