#!/usr/bin/env python3
"""Summarize the differences between two sets of geocodes.

Usage:

    ./oldtoronto/diff_geocodes.py old/geocode_results.json data/geocode_results.json

This works best if you copy the version of data/geocode_results.json on the master branch to a
temp location and run against the version in your branch.
"""

import argparse
import json
import random

from haversine import haversine

from utils.id_sample import should_sample


def diff_geocodes(args):
    old = json.load(open(args.before))
    new = json.load(open(args.after))

    num_samples = args.num_samples
    sampling_rate = args.sample

    old_ids = {k for k in old.keys() if should_sample(k, sampling_rate)}
    new_ids = {k for k in new.keys() if should_sample(k, sampling_rate)}
    dropped_ids = old_ids.difference(new_ids)
    added_ids = new_ids.difference(old_ids)
    changed_ids = [
        k
        for k in new_ids.intersection(old_ids)
        if old[k]['lat'] != new[k]['lat'] or old[k]['lng'] != new[k]['lng']
    ]

    print(f'''
  Before: {len(old_ids):,}
   After: {len(new_ids):,}

   Added: {len(added_ids):,}
 Dropped: {len(dropped_ids):,}
 Changed: {len(changed_ids):,}
    ''')

    print('\nSample of additions:')
    add_samples = min(args.num_add_samples or num_samples, len(added_ids))
    for k in random.sample(added_ids, add_samples):
        b = new[k]
        print(f' {k:6}: {b["original_title"]}')
        print(f'   + {b.get("lat"):.6f},{b.get("lng"):.6f} {b.get("technique")}')

    print('\nSample of dropped:')
    drop_samples = min(args.num_drop_samples or num_samples, len(dropped_ids))
    for k in random.sample(dropped_ids, drop_samples):
        a = old[k]
        print(f' {k:6}: {a["original_title"]}')
        print(f'   - {a.get("lat"):.6f},{a.get("lng"):.6f} {a.get("technique")}')

    print('\nSample of changes:')
    changed_samples = min(args.num_changed_samples or num_samples, len(changed_ids))
    for k in random.sample(changed_ids, changed_samples):
        a = old[k]
        b = new[k]
        a_lat = a.get('lat')
        a_lng = a.get('lng')
        b_lat = b.get('lat')
        b_lng = b.get('lng')
        d_meters = haversine((a_lat, a_lng), (b_lat, b_lng)) * 1000

        print(f' {k:6}: {a["original_title"]}')
        print(f'   - {a_lat:.6f},{a_lng:.6f} {a.get("technique")}')
        print(f'   + {b_lat:.6f},{b_lng:.6f} {b.get("technique")}')
        print(f'     Moved {d_meters:0,.0f} meters')


if __name__ == '__main__':
    parser = argparse.ArgumentParser('Analyze the differences between two sets of geocodes.')
    parser.add_argument('--sample', type=float,
                        help='Process a deterministic sample of images. 1=100%%, 0.1=10%%, etc.',
                        default=1.0)
    parser.add_argument('--num_samples', type=int,
                        help='Number of examples of each type (add, drop, change) to show.',
                        default=20)
    parser.add_argument('--num_add_samples', type=int,
                        help='Number of added images to show (defaults to --num_samples).',
                        default=0)
    parser.add_argument('--num_drop_samples', type=int,
                        help='Number of dropped images to show (defaults to --num_samples).',
                        default=0)
    parser.add_argument('--num_changed_samples', type=int,
                        help='Number of changed images to show (defaults to --num_samples).',
                        default=0)
    parser.add_argument('before', help='Path to geocode_results.json before', type=str)
    parser.add_argument('after', help='Path to geocode_results.json after', type=str,
                        default='data/geocode_results.json')
    args = parser.parse_args()

    diff_geocodes(args)
