#!/usr/bin/env python3
"""This script generates an ndjson file for the Toronto Public Library.

It fetches and parses Toronto Public Library XML results.

Usage:

    oldtoronto/parse_library_xml.py data/tpl/tpl-rss-urls.txt data/tpl/toronto-library.ndjson

The choice of field names is somewhat evocative of the Toronto Archives.
"""

import json
import sys
import xml.etree.ElementTree as ET

import fetcher


def parse_library_item(item_et):
    """Convert an item XML etree into a JSON object."""
    r = item_et.find('record')
    attrs = {}
    for attr in r.find('attributes').findall('attr'):
        name = attr.get('name')
        if name in attrs:
            attrs[name] += '\n' + attr.text
        else:
            attrs[name] = attr.text

    id_ = r.find('recordId').text
    o = {
        'title': item_et.find('title').text,
        'title_alt': attrs.get('p_dig_title_alternate'),
        'url': item_et.find('link').text,
        'uniqueID': id_,
        'creator': attrs.get('p_dig_creator'),
        'license': attrs.get('p_dig_license'),
        'access': attrs.get('p_dig_access_rights'),
        'provenance': attrs.get('p_dig_provenance'),
        'date': attrs.get('p_dig_pub_date'),
        'subject': attrs.get('p_dig_subject_topical'),
        'location': attrs.get('p_dig_tslocation'),
        'description': attrs.get('p_dig_description'),
        'rights_holder': attrs.get('p_dig_rights_holder'),
        'imageLink': 'https://static.torontopubliclibrary.ca/da/images/MC/%s' % (
            attrs.get('p_file_name').lower())
    }
    return o


def parse_library_results_xml(xml_str):
    """Parse RSS results from the Toronto Public Library."""
    root = ET.fromstring(xml_str)
    results = []
    for item in root[0].findall('item'):
        results.append(parse_library_item(item))
    return results


if __name__ == '__main__':
    urls_file_input, ndjson_output = sys.argv[1:]
    f = fetcher.Fetcher()
    out = open(ndjson_output, 'w')
    ids = set()
    for num, url in enumerate(open(urls_file_input)):
        url = url.strip()

        if not f.is_url_in_cache(url):
            continue

        xml = f.fetch_url_from_cache(url).decode('utf8')
        records = parse_library_results_xml(xml)
        for record in records:
            id_ = record['uniqueID']
            if id_ in ids:
                continue
            json.dump(record, out)
            out.write('\n')
            ids.add(id_)

        sys.stderr.write('Processed %d results...\n' % (1 + num))
