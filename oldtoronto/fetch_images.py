#!/usr/bin/env python3
"""Download all the images referenced from an images.ndjson file.

Usage: ./fetch_images.py images.ndjson
"""

import fileinput
import json
import os

import requests

import fetcher

if __name__ == '__main__':
    f = fetcher.Fetcher()
    os.makedirs('images', exist_ok=True)

    for i, line in enumerate(fileinput.input()):
        image = json.loads(line)
        url = image.get('imageLink')
        if not url:
            continue
        path = os.path.join('images', os.path.basename(url))
        if os.path.exists(path):
            continue
        try:
            content = f.fetch_url(url)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                continue  # sadly, some images are just missing
            raise

        open(path, 'wb').write(content)
        if i > 0 and i % 20 == 0:
            print('Fetched %d images' % i)
