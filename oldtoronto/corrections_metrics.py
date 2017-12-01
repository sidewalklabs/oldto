#!/usr/bin/env python3
"""Calculate the difference between geocodes and some truth data in a csv.

The input consistss of a truth csv (without a header) of imageId,lat,lng and some geocode_results.
The script checks to see how many of calculated lat, lngs are corrected in comparision to the
truth csv. Incorrect image ids get saved to a csv and correct image ids get printed to stderr.

Geocodes
    - Missing a location
    - Have a location where there should be none
    - Location is far (>250m?) from true location. Bullseye = within 25m?
    - Not Geocodable. geocode.py did not find any lat, lng.
"""
import argparse
import csv
import json
import sys

from calculate_metrics import diff_geocode


def check_against_truth_data(geocodes, truth):
    correct = []
    incorrect = []
    for row in truth:
        image_id = row['image_id']
        geocode_result = geocodes.get(image_id)
        if geocode_result:
            geocode_lat = geocode_result['lat']
            geocode_lng = geocode_result['lng']
            is_same, error_reason = diff_geocode((float(row['lng']), float(row['lat'])),
                                                 (geocode_lng, geocode_lat))
            if is_same:
                correct.append(image_id)
            else:
                incorrect.append((image_id, error_reason))
        else:
            incorrect.append((image_id, 'Not Geocodable'))
    return correct, incorrect


def main(geocodes_json_path, truth_csv_path, incorrect_file):
    geocodes = json.load(open(geocodes_json_path))
    with open(truth_csv_path) as csv_file:
        truth = csv.DictReader(csv_file, ['image_id', 'lat', 'lng'])
        corrected_ids, incorrect_geocodes = check_against_truth_data(geocodes, truth)
        with open(incorrect_file, 'w') as csv_file:
            writer = csv.writer(csv_file)
            for incorrect in incorrect_geocodes:
                writer.writerow(incorrect)
        for correct in corrected_ids:
            sys.stderr.write(f'{correct}\n')
        sys.stderr.write('\n\n\n\n\n')
        total_ids = len(corrected_ids) + len(incorrect_geocodes)
        sys.stderr.write(f'corrected ids: {len(corrected_ids)} / {total_ids}\n')
        sys.stderr.write(f'inncorrect ids: {len(incorrect_geocodes)} / {total_ids}\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        'Check lat, lngs against a csv of truth data, print out matches.')
    parser.add_argument('--geocodes', type=str,
                        help='file calculated by geocode.results',
                        default='data/corrections.geocode_results.json')
    parser.add_argument('--truth_data', type=str,
                        help='CSV file (without a header line) of imageId,lat,lng',
                        default='data/corrections.csv')
    parser.add_argument('--incorrect_file', type=str,
                        help='file to write a csv of image_id,error_reason',
                        default='data/incorrect.csv')
    args = parser.parse_args()

    main(args.geocodes, args.truth_data, args.incorrect_file)
