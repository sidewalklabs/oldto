#!/usr/bin/env python3
"""Parse out metadata for individual images from the image details page.

Input:  records.txt (list of IDs for individual record pages)
Output: records.ndjson

Usage:

    ./parse_records.py record-ids.txt records.ndjson

Note that all URLs are assumed to have been cached beforehand, e.g. with:

    ./fetch_archive_records.py record-ids.txt
"""

import json
import re
import sys
from bs4 import BeautifulSoup

import fetcher
from toronto_archives import url_for_unique_id

keys = {
    'Access conditions': 'condition',
    'Administrative history or biographical sketch': 'history',
    'Anticipated additions to the records': 'anticipated_additions',
    'Archival citation': 'citation',
    'Author or Creator': 'author',
    'Comments': None,
    'Copyright conditions': 'copyright',
    'Custodial history': 'custodial_history',
    'Date(s) of creation of record(s)': 'date',
    'Edition': 'edition',
    'Finding aids': 'finding_aids',
    'Form of material': 'form',
    'Forms part of': 'part_of',
    'Forms part of (Links)': 'part_of_links',
    'General note(s)': 'notes',
    'Language note': 'language_notes',
    'Note about date(s) of creation': 'date_notes',
    'Notes about author or creator': 'author_notes',
    'Notes about physical description': 'physical_desc_notes',
    'Notes about title': 'title_notes',
    'Note regarding exhibition or publication of the records': 'publication_notes',
    'Numbers or letters borne by the records': 'numbers',
    'Other relevant information': 'other',
    'Physical description of record(s)': 'physical_desc',
    'Publication information': 'publication_info',
    'Record consists of': 'consists_of',
    'Record consists of (Links)': 'consists_of_links',
    'Scope and content': 'scope',
    'Subjects': 'subject',
    'Title': 'title',
    'Scale': 'scale',
    'To request records at the archives': None,
    'Terms governing use': 'terms',
    'imageLink': 'imageLink'
}

# Labels for which we want to extract links.
link_labels = {
    'Forms part of',
    'Record consists of'
}


def machine_keys(tags):
    """Convert human-readable Toronto archive tags to machine names."""
    out = {}
    for k, v in tags.items():
        new_k = keys[k.strip()]
        if new_k:
            out[new_k] = v
    return out


def parse_html(html):
    """Parse a single record page."""
    soup = BeautifulSoup(html, 'html.parser')
    tags = {}
    for row in soup.select('.row'):
        labels = row.select('#displayLabel')
        data = row.select('#displayData')
        if len(labels) == 0:
            continue
        assert len(labels) == len(data)
        label = labels[0].text
        values = [div.text for div in data]
        tags[label] = '\n'.join(values)
        links = data[0].select('a') if data and data[0] else []
        if len(links) > 0 and label in link_labels:
            tags[label + ' (Links)'] = [
                (extractId(link['href']), link.text)
                for link in links
            ]

    imgs = soup.select('a.img-thumbnail')
    if len(imgs) == 1:
        tags['imageLink'] = 'https://gencat4.eloquent-systems.com:443%s' % imgs[0]['href']

    return machine_keys(tags)


def extractId(url):
    m = re.search(r'KEY_(\d+)', url)
    assert m, 'No id in %s' % url
    return m.group(1)


if __name__ == '__main__':
    (urls_file_input, ndjson_output) = sys.argv[1:]
    f = fetcher.Fetcher()
    out = open(ndjson_output, 'w')
    for num, id_ in enumerate(open(urls_file_input)):
        id_ = id_.strip()

        url = url_for_unique_id(id_)
        if not f.is_url_in_cache(url):
            continue

        html = f.fetch_url_from_cache(url).decode('utf8')
        tags = parse_html(html)
        tags['uniqueID'] = id_
        out.write(json.dumps(tags))
        out.write('\n')

        if num > 0 and num % 1000 == 0:
            sys.stderr.write('Parsed %d records...\n' % num)
