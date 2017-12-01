#!/usr/bin/env python3
"""Write out a list of URLs for records.txt.

This consumes an ndjson file of images and generates URLs to retrieve to get complete
image metadata.

Usage:

    ./write_records_txt.py images.random1000.ndjson > record-ids.txt

"""

import fileinput
import json

if __name__ == '__main__':
    for line in fileinput.input():
        record = json.loads(line)
        if 'uniqueID' in record:
            print(record['uniqueID'])
