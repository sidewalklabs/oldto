#!/usr/bin/env python3
"""Write out a list of URLs to fetch for each file/subseries/series.

Usage:

    ./write_all_series_txt.py > series.txt

Running the fetcher & parser on this file will then yield series.ndjson, which contains
information on all the files, subseries, series and fonds in the archive.
"""

import json

records = [
    json.loads(line)
    for line in open('record-per-file.ndjson')
]

for record in records:
    links = record.get('part_of_links')
    if not links:
        continue
    for id_, text in links:
        print(id_)
