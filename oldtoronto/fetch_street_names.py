#!/usr/bin/env python3
"""Saves a list of known street names from the city of toronto."""
import bs4
import requests


STREET_NAMES_URL = 'https://geographic.org/streetview/canada/on/city_of_toronto.html'
OUTPUT_FILENAME = 'data/streets.txt'


def main():
    response = requests.get(STREET_NAMES_URL)
    if response.status_code == 200:
        soup = bs4.BeautifulSoup(response.text, 'html.parser')
        street_names = [li.text for li in soup.find_all('li')]
        with open(OUTPUT_FILENAME, 'w') as f:
            f.write('\n'.join(street_names))


if __name__ == '__main__':
    main()
