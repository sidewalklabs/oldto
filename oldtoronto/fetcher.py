#!/usr/bin/env python
"""Fetch a bunch of URLs and store them permanently on-disk.

This does rate-throttling.

The cache key is the URL. URLs are stored in a directory correspoding with their
hostname and under their MD5 hash to avoid issues with escaping URLs in file names.
The storage format on disk is

  cache/
    urls.txt
    hostname.com/MD51
    hostname.com/MD52
    www.google.com/MD53
    ...

Usage:
    ./fetcher.py path-to-list-of.urls.txt
"""

import fileinput
import hashlib
import io
import json
import os
import sys
import time
import urllib

import requests


class NotInCacheError(Exception):
    pass


class Response(object):
    contents = bytes()
    status_code = 200

    def json(self):
        return json.load(io.BytesIO(self.contents))


class CacheSession(requests.Session):
    """Monkey patch this is to replace requests.Session in order to cache get requests."""
    def __init__(self, cache=None):
        super(CacheSession, self).__init__()
        self._cache = cache if cache else Cache()

    def send(self, request, **kwargs):
        url = request.url
        assert request.method == 'GET'
        resp = None
        if self._cache.is_url_in_cache(url):
            resp = Response()
            resp.contents = self._cache.fetch_url_from_cache(url)
        else:
            resp = super(CacheSession, self).send(request, **kwargs)
            self._cache.store_url_in_cache(url, resp.content)
        return resp


class Cache(object):
    """Store get request responses, keyed by their url."""
    def __init__(self, cache_dir='cache'):
        super(Cache, self).__init__()
        self._cache_dir = cache_dir
        os.makedirs(self._cache_dir, exist_ok=True)
        self._urls_file = os.path.join(self._cache_dir, 'urls.txt')

    def _cache_path(self, url):
        """Returns path to the cached version of an URL, regardless of whether it exists."""
        parsed_url = urllib.parse.urlparse(url)
        dir_path = os.path.join(self._cache_dir, parsed_url.netloc)
        return os.path.join(dir_path, self._hash(url))

    def _hash(self, url):
        """Compute SHA1 checksum for the URL."""
        return hashlib.sha1(url.encode('utf8')).hexdigest()

    def fetch_url_from_cache(self, url):
        path = self._cache_path(url)
        if not os.path.exists(path):
            raise NotInCacheError()
        return open(path, 'rb').read()

    def is_url_in_cache(self, url):
        return os.path.exists(self._cache_path(url))

    def store_url_in_cache(self, url, contents):
        path = self._cache_path(url)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        open(path, 'wb').write(contents)
        open(self._urls_file, 'a').write('%s\t%s\n' % (self._hash(url), url))

    def remove_url_from_cache(self, url):
        # Note: we leave the URL in cache/urls.txt. It's harmless there.
        path = self._cache_path(url)
        if os.path.exists(path):
            os.unlink(path)


class Fetcher(object):
    """Provides throttling on top of the cache object."""
    def __init__(self, throttle_secs=3.0, cache_dir='cache'):
        self._cache = Cache(cache_dir)
        self._throttle_secs = throttle_secs
        self._last_fetch = 0.0

    def fetch_url(self, url, force_refetch=False):
        if force_refetch:
            self._cache.remove_url_from_cache(url)
        try:
            return self._cache.fetch_url_from_cache(url)
        except NotInCacheError:
            pass

        t = time.time()
        if t - self._last_fetch < self._throttle_secs:
            wait_s = self._throttle_secs - (t - self._last_fetch)
            sys.stderr.write('Waiting %s secs...\n' % wait_s)
            time.sleep(wait_s)

        print('Fetching %s...' % url)
        self._last_fetch = time.time()
        response = requests.get(url)
        response.raise_for_status()  # checks for status == 200 OK

        contents = response.content
        self._cache.store_url_in_cache(url, contents)
        return contents

    def is_url_in_cache(self, url):
        return self._cache.is_url_in_cache(url)

    def fetch_url_from_cache(self, url):
        return self._cache.fetch_url_from_cache(url)

    def remove_url_from_cache(self, url):
        # Note: we leave the URL in cache/urls.txt. It's harmless there.
        self._cache.remove_url_from_cache(url)


if __name__ == '__main__':
    f = Fetcher()
    for i, line in enumerate(fileinput.input()):
        line = line.strip()
        if '\t' in line:
            filename, url = line.split('\t')
        else:
            filename = None
            url = line

        print('%5d Fetching %s' % (i + 1, url))
        content = f.fetch_url(url)
        if filename:
            open(filename, 'wb').write(content)
        print('  %d bytes' % len(content))
