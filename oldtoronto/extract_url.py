#!/usr/bin/env python
"""Debug tool to read a single URL from the sqlite cache.

Usage:

    ./extract_url.py http://example.com > example.html

This throws if the URL is not in the cache.
"""

import sys

import fetcher


def main():
    (_, url) = sys.argv
    f = fetcher.Fetcher()
    content = f.fetch_url_from_cache(url)
    sys.stderr.write('Loading cached content from %s\n' % f._cache_path(url))
    print(content.decode('utf8'))


if __name__ == '__main__':
    main()
