#!/usr/bin/env python3
"""Attach relevant information from small Files/Subseries to parent ndjson records.

"""

import json
import re
import sys


def load_series():
    """Returns a uniqueID --> series record dict."""
    out = {}
    for line in open('data/series.ndjson'):
        record = json.loads(line)
        id_ = record['uniqueID']
        out[id_] = record
    return out


if __name__ == '__main__':
    input_path, output_path = sys.argv[1:]

    id_to_series = load_series()

    with open(output_path, 'w') as out:
        for line in open(input_path):
            record = json.loads(line)
            id_ = record['uniqueID']
            if not record['title']:
                continue  # filter out empty records
            if 'part_of_links' not in record:
                sys.stderr.write(id_ + '\n')
            parents = record.get('part_of_links')[0]
            assert parents, id_
            (parent_id, parent_name) = parents
            record['parent_uniqueID'] = parent_id

            if re.match(r'^File|Subseries', parent_name):
                parent = id_to_series.get(parent_id)
                if not parent:
                    sys.stderr.write(
                        'Missing parent: %s: %s for %s\n' % (parent_id, parent_name, id_))
                else:
                    record['parent_date'] = parent['date']
                    record['parent_desc'] = parent.get('physical_desc', '')
                    record['parent_title'] = parent['title']
                    record['parent_scope'] = parent.get('scope', '')
            out.write(json.dumps(record))
            out.write('\n')
