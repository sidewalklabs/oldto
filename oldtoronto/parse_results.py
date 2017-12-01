#!/usr/bin/env python
"""Parse light image metadata out of search results pages.

Inputs: results.txt (list of search result page URLs)
        sqlite database of scraped URLs
Output: images.ndjson

Usage: ./parse_results.py
"""

import json
import re
import urllib
import urllib.parse

from bs4 import BeautifulSoup

import fetcher


def lines_from_html(html):
    lines = html.split('\n')
    lines = [line for line in lines
             if 'webcat/systems/toronto.arch/resource' in line and 'citation' in line]
    return lines


def extract_from_line(line):
    m = re.search(r'^ *\+ \'(.*)\';|', line)
    html = urllib.parse.unquote(m.group(1))
    soup = BeautifulSoup(html, 'html.parser')

    tags = {}
    for row in soup.select('.cartData'):
        label = row['id']
        data = row.text
        tags[label] = data

    return tags


if __name__ == '__main__':
    f = fetcher.Fetcher()

    out = open('data/images.ndjson', 'w')

    for url in open('results.txt'):
        url = url.strip()
        print(url)
        if not f.is_url_in_cache(url):
            continue

        html = f.fetch_url_from_cache(url).decode('utf8')
        lines = lines_from_html(html)
        for line in lines:
            tags = extract_from_line(line)
            out.write(json.dumps(tags))
            out.write('\n')
