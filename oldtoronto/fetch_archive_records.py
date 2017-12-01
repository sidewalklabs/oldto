#!/usr/bin/env python3
"""Use the cached fetcher to retrieve records from the Toronto Archives.

Usage:

    ./fetch_archive_records.py list-of-ids.txt

These can then be parsed into an ndjson file with parse_records.py.
"""

import fileinput

import fetcher
from toronto_archives import url_for_unique_id


if __name__ == '__main__':
    f = fetcher.Fetcher(throttle_secs=2.0)
    any_uncached_fetches = False
    for i, line in enumerate(fileinput.input()):
        id_ = line.strip()
        url = url_for_unique_id(id_)
        in_cache = f.is_url_in_cache(url)
        if in_cache and not any_uncached_fetches:
            # Skip leading cached fetches to reduce logging verbosity.
            continue
        print('%5d Fetching %s: %s' % (i + 1, id_, url))
        any_uncached_fetches = True
        content = f.fetch_url(url)
        print('  %d bytes%s' % (len(content), ' (cached)' if in_cache else ''))
