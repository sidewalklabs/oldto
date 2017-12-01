from nose.tools import eq_
from parameterized import parameterized

import sys

sys.path.append('oldtoronto')
from oldtoronto.date_distribution import parse_year # noqa


@parameterized([
    (('1915', '1915'), 'May 20, 1915'),
    (('1922', '1922'), '[ca. June 1922]'),
    (('1890', '1890'), '[ca. 1890]'),
    (('1947', '1947'), '[ca. July 1947]'),
    (('1920', '1929'), '[192-]'),
    ((None, '1900'), '[before 1900]'),
    (('1900', None), '[after 1900]'),
    (('1946', '1946'), '1946'),
    (('1945', '1952'), '[ca. 1945-52]'),
    (('1940', '1949'), '[194-?]'),
    (('1958', '1958'), '[ca. February 8, 1958-?]'),
    (('1948', '1948'), '[ca. 1948-?]'),
    (('1900', '1910'), '[between 1900 and 1910?]'),
    (('1900', '1910'), '[between 1900? and 1910?]'),
    (('1900', '1910'), '[betwen 1900 and 1910?]'),
    (('1920', '1940'), '[between 1920? anad 1940]'),
    (('1939', '1940'), '1939 or 1940'),
    (('1950', '1959'), '[ 195-?]'),
    (('1950', '1959'), '[195?]'),
    (('1960', '1960'), '[Summer 1960]'),
    (('1963', '1972'), '1963 - 1972'),
    (('1962', '1962'), '[ca.1962]'),
    (('1962', '1962'), 'circa 1962'),
    (('1939', '1945'), '[between 1939-1945]'),
    (('1989', '1990'), '[between 1989 or 1990]'),
    (('1924', '1924'), 'Digitized 2010 (originally created November 9, 1924)'),
    (('1960', '1960'), '[1960?].'),
    (('1942', '1942'), 'November 23 & 24, 1942'),
    (('1923', '1923'), 'Febuary 16, 1923'),
    (None, 'Digitized 2010'),
    (('1948', '1948'), 'June 15-19, 1948')
    # Patterns that don't work yet:
    # (('1964', '1980'), '[between ca. 1964 and 1980]')
])
def test_parse_year(expected_year, input_text):
    eq_(expected_year, parse_year(input_text))
