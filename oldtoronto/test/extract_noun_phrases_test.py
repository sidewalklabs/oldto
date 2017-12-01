from nose.tools import eq_
from parameterized import parameterized

from ..extract_noun_phrases import extract_nouns, is_street


@parameterized([
    ('Humane Society Parade, Pinto, 53 years old, head',
        ['Humane Society Parade', 'Pinto']),
    ('Holiday trip, roadside oven, Marjorie Laing, en route to Rimouski',
        ['Marjorie Laing', 'Rimouski']),
    ('Carol Turofsky', ['Carol Turofsky']),
    ('Construction of retaining wall on railway lands, Chaplin Cres. north of Eglinton Ave. W.',
        ['Chaplin Cres.', 'Eglinton Ave. W.']),
    ('Corner of Jarvis St. and Lakeshore Blvd., looking south-east',
        ['Jarvis St.', 'Lakeshore Blvd.']),
    ('Waterfront landfill 1834-1981', []),
    ('Kennedy Road', ['Kennedy Road']),
    ('C. N. E. Horse Stables', ['C. N. E. Horse Stables']),
    ('Pouring concrete, Aylmer Avenue Bridge', ['Aylmer Avenue Bridge'])
])
def test_extract_nouns(phrase, expectation):
    eq_(expectation, extract_nouns(phrase))


@parameterized([
    ('Eglinton Avenue East', True),
    ('Eglinton Avenue', True),
    ('Yonge Street', True),
    ('Metropolitan Toronto', False),
    ('High Park', False),
    ('Aylmer Avenue Bridge', False),
    ('Queen Street West', True),
    ('Don Valley Parkway', True),
    ('Lake Shore Blvd', True),
    ('Remembrance Drive', True),
    ('Front St E.', True)
])
def test_is_street(phrase, expectation):
    eq_(expectation, is_street(phrase))
