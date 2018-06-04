#!/usr/bin/env python
"""Filter out Toronto Public Library images from the Toronto Star.

These have a more restrictive license and may not be shown outside of the
Toronto Public Library's website.

Usage:

    ./oldtoronto/filter_star_images.py images.ndjson > images-nonstar.ndjson
"""

import fileinput
import json
import sys


def is_star_image(record):
    # There are a few ways to identify Toronto Star images.
    # The 'provenance' and 'rights_holders' fields are sometimes set to None.
    return (
        'TSPA' in record['license'] or
        '-TS-' in record['uniqueID'] or
        'Toronto Star' in (record['provenance'] or []) or
        'Toronto Star' in (record['rights_holder'] or []))


if __name__ == '__main__':
    num_star = 0
    num_total = 0
    num_output = 0
    for row in fileinput.input():
        record = json.loads(row)
        num_total += 1
        if is_star_image(record):
            num_star += 1
            continue
        num_output += 1
        print(row, end='')
    sys.stderr.write('Total records: %6d\n' % num_total)
    sys.stderr.write(' Star records: %6d\n' % num_star)
    sys.stderr.write('    Remaining: %6d\n' % num_output)
