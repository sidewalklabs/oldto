#!/usr/bin/env python3
"""Write out a set of thick record URLs to fetch, one per File/Series/etc.

The idea here is that there's valuable data on the File/Subseries pages, but we have no way of
figuring out what the unique ID for the series is without fetching the record page for an image
belonging to it. This script assembles a minimal set of IDs that should get us links to all the
series pages.

Usage:

    ./write_record_url_per_file.py > record-per-file.txt
"""

import json
import sys

from toronto_archives import get_citation_hierarchy


INPUT_FILE = 'data/images.ndjson'

if __name__ == '__main__':
    seen_prefixes = set()

    for line in open(INPUT_FILE):
        image = json.loads(line)
        uniqueId = image.get('uniqueID')
        if not uniqueId:
            continue
        citations = image['citations']
        hierarchy = get_citation_hierarchy(citations)
        if len(hierarchy) == 0:
            sys.stderr.write('No hierarchy for "%s"\n' % citations)
            continue
        prefix = hierarchy[0]
        if prefix in seen_prefixes:
            continue
        seen_prefixes.add(prefix)
        print(uniqueId)
