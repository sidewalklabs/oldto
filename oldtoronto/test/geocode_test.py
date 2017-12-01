import json
import tempfile
import sys

sys.path.append('oldtoronto')

from nose.tools import eq_, ok_ # noqa
from parameterized import parameterized # noqa
from oldtoronto import geocode # noqa


class MapsClientMock(object):
    def geocode(self, search_term):
        search_term_to_response = {
            'Davenport Road and Uxbridge Avenue ontario toronto canada': [{
                'formatted_address': 'Uxbridge Ave & Davenport Rd, Toronto, ON M6N, Canada',
                'geometry': {
                    'location': {'lat': 43.6701965, 'lng': -79.45703689999999},
                    'location_type': 'GEOMETRIC_CENTER'
                },
                'place_id': 'EjRVeGJyaWRnZSBBdmUgJiBEYXZlbnBvcnQgUmQsIFRvcm9udG8',
                'types': ['intersection']
            }],
            '203 church street ontario toronto canada': [{
                'formatted_address': '203 Church St, Toronto, ON M5B 1Y7, Canada',
                'geometry': {
                    'location': {'lat': 43.6558684, 'lng': -79.3766057},
                    'location_type': 'ROOFTOP'
                },
                'place_id': 'ChIJq0vJsjXL1IkRwl1yV0h5TzQ',
                'types': ['street_address']
            }],
            '161 beatrice street ontario toronto canada': [{
                'formatted_address': '161 Beatrice St, Toronto, ON M6G 1B9, Canada',
                'geometry': {
                    'location': {'lat': 43.655123, 'lng': -79.41658699999999},
                    'location_type': 'RANGE_INTERPOLATED'
                },
                'place_id': 'EiwxNjEgQmVhdHJpY2UgU3QsIFRvcm9udG8sIE9OIE02RyAxQjksIENhbmFkYQ',
                'types': ['street_address']
            }]
        }
        return search_term_to_response.get(search_term, [])


images = [
    {
        'title': 'Rear of 203 Church Street leaning wall',
        'date': 'November 27, 1914',
        'uniqueID': '100001',
    },
    {
        'title': '161 Beatrice Street',
        'date': 'December 10, 1914',
        'uniqueID': '100004',
    },
    {
        'title': 'Northwest corner Davenport Road and Uxbridge Avenue - Defective building',
        'date': 'April 17, 1915',
        'uniqueID': '100007',
    },
    {
        'title': 'Princess Theatre ruins after fire',
        'date': 'May 10, 1915',
        'uniqueID': '100022',
    },
    {
        'title': 'C. N. E. - Grandstand',
        'date': 'May 10, 1915',
        'uniqueID': '100023',
    },
    {
        'title': 'High Park benches',
        'date': 'May 10, 1915',
        'uniqueID': '100024',
    }
]

street_names = [
    'Bathurst Street',
    'Bathurst St.',
    'Beatrice Street',
    'Beech Avenue',
    'Bloor Street',
    'Carlaw Street',
    'church street',
    'clinton street',
    'davenport road',
    'Dufferin Street',
    'Erin Street',
    'Eglinton Avenue',
    'lake shore',
    'marjory avenue',
    'McLean Avenue',
    'medland crescent',
    'myrtle avenue',
    'Queen Street East',
    'Queen St. E.',
    'Richmond St',
    'Richmond St E.',
    'richmond street west',
    'spadina avenue',
    'st clair avenue west',
    'uxbridge avenue',
    'Victoria St',
    'wells hill road',
    'yonge street',
]

pois = [
    'name,osmid,lat,lng,score,type',
    'C. N. E.,1000000004164234,43.633751,-79.4192546,2,tourism:theme_park',
    'CNE,1000000004164234,43.633751,-79.4192546,2,tourism:theme_park',
    'High Park,1000000014344414,43.6462345,-79.4627137,1,leisure:park'
]

toronto_street_re_str = geocode.build_is_a_toronto_street_regex_str(street_names)
exact_address_regex = geocode.exact_address_regex(toronto_street_re_str)
standalone_street_re = geocode.standalone_street_regex(toronto_street_re_str)


@parameterized([
    ('Queen Street East', True),
    ('Queen Street East, ', True),
    ('Queen Street Easter', False),
    ('Richmond St E., view ', True)
])
def test_standalone_street_regex(text, should_match):
    m = standalone_street_re.search(text)
    does_match = not not m
    eq_(does_match, should_match)


@parameterized([
    ('Lakeshore, west from Lee Ave', ('Lakeshore', 'Lee Ave')),
    ('Spadina Avenue looking north from Wellington Street',
     ('Spadina Avenue', 'Wellington Street')),
    ('Toronto Street looking north from King Street', ('Toronto Street', 'King Street')),
    ('Yonge pedestrian mall looking north from Queen', None),
    ('Elm [?] looking west from Yonge', ('Elm', 'Yonge')),
    ('Looking north from King, east of York St', ('King', 'York St')),
    ('Yonge looking south from north of Roxborough', ('Yonge', 'Roxborough')),
    ('Sunnyside crossing looking west from bridge', None),
    ('Bay looking north from Queen', ('Bay', 'Queen')),
    ('King West looking east from west of Peter', ('King West', 'Peter')),
    ('Yonge looking south from College', ('Yonge', 'College')),
    ('Yonge looking north from Davisville', ('Yonge', 'Davisville')),
    ('Yonge Street looking north from opposite Adelaide Street',
     ('Yonge Street', 'Adelaide Street')),
    ('Front looking east from Jarvis', ('Front', 'Jarvis')),
    ('View of College Street looking east from Bathurst Street',
     ('College Street', 'Bathurst Street')),
    ('Yonge looking north from south of Gould [?]', ('Yonge', 'Gould')),
    ('Dufferin Street looking south from opposite 561', None),
    ('Looking north from near 1439 Yonge', None),
    ('View of Dundas Street West looking east from bridge at College Street',
     ('Dundas Street West', 'College Street')),
    ('Eastern Beaches, east from Kippendavie Avenue', ('Eastern Beaches', 'Kippendavie Avenue')),
    ('Dufferin Street north from opposite 1667', None),
    ('Harbour Industrial Railway, Don Roadway looking south from Queen Street',
     ('Don Roadway', 'Queen Street')),
    ('Waterfront at High Park and Humber looking north from above', None),
    ('College looking west from west of Yonge ', ('College', 'Yonge')),
    ('Elm looking west from Yonge', ('Elm', 'Yonge')),
    ('Toronto skyline - looking east', None),
    ('Yonge Street north from Front Street', ('Yonge Street', 'Front Street')),
    ('Close up of railway yards looking east from Bathurst Street', None),
    ('College Street looking east from Bathurst Street', ('College Street', 'Bathurst Street')),
    ('Bayview looking north from Manor', ('Bayview', 'Manor')),
    ('Old crib north from M.P.S. (foot of John Street in tunnel)', None),
    ('King looking west from Bay', ('King', 'Bay')),
    ('Railway lands looking west from Spadina from above', None),
    ('Toronto Street, looking north from King Street', ('Toronto Street', 'King Street')),
    ('Gould looking east from Yonge at night', ('Gould', 'Yonge')),
    ('King Street : looking east across Yonge Street', ('King Street', 'Yonge Street')),
    ('Trestle east from Cherry Street', ('Trestle', 'Cherry Street')),
    ('Streetcar on Queens Quay looking east to Rees', ('Queens Quay', 'Rees')),
    ('Queen’s Wharf Lighthouse on Fleet Street, west of Bathurst Street',
     ('Fleet Street', 'Bathurst Street')),
    ('Kingston Rd, east from Woodbine', ('Kingston Rd', 'Woodbine'))
])
def parse_direction_from_test(original, match):
    result = geocode.parse_direction_from(original)
    if result:
        method, search_term, match_result, expected_type = result
        eq_(match_result[0], 'looking')
        match_result = match_result[1:]
        eq_(match_result, match)
        eq_(geocode.INTERSECTION_TYPE, expected_type)
    else:
        eq_(result, match)


@parameterized([
    ('Bathurst Street looking southeast at Davenport Road',
        ('Bathurst Street and Davenport Road')),
    ('Bathurst Street and Davenport Road look southeast', ('Bathurst Street and Davenport Road')),
    ('Yonge Street south from Bloor Street', ('Yonge Street and Bloor Street')),
    ('Bathurst Street north over Davenport Road', ('Bathurst Street and Davenport Road')),
    ('Queen Street East from Hammersmith to McLean Avenue',
        ('Queen Street East and McLean Avenue')),
    ('View of Queen Street East, looking west at Carlaw Street',
        ('Queen Street East and Carlaw Street')),
    ('Richmond St E., view is west across Victoria St',
        ('Richmond St E. and Victoria St')),
    ('Northwest corner Davenport Road and Uxbridge Avenue — Defective building',
        ('Davenport Road and Uxbridge Avenue'))
])
def parse_two_streets_test(original, result):
    method, search_term, _, expected_type = \
        geocode.parse_two_streets(standalone_street_re, original)
    eq_(method, 'google')
    eq_(search_term.split(' ontario')[0], result)
    eq_(geocode.INTERSECTION_TYPE, expected_type)


@parameterized([
    ('161 Beatrice Street', '161 beatrice street'),
    ('82 Medland Crescent', '82 medland crescent'),
    ('14 Wells Hill Road — Boiler explosion (cellar)', '14 wells hill road'),
    ('28-30 Marjory Avenue', '30 marjory avenue'),
    ('176 Lake Shore, Island', '176 lake shore'),
    ('Rear 9-15 1/2 Myrtle Avenue — Barn', '15 myrtle avenue'),
    ('Victory Building, 78-82 Richmond Street West — Supports', '82 richmond street west'),
    ('Rear of 470-472 Spadina Avenue', '472 spadina avenue'),
    ('Rear of 470 Spadina Avenue', '470 spadina avenue'),
    ('127 Bathurst St.', '127 bathurst st.'),
    ('345, 347, 349, 351 Beech Avenue', '351 beech avenue'),
    ('305 1/2 Clinton Street', '305 clinton street'),
    ('717  1/2 Queen St. E. - plumbing', '717 queen st. e.'),
    ('North side 235.5 Yonge Street 1954', '235.5 yonge street'),
])
def extract_exact_address_test(original, result):
    method, search_term, _, expected_type = \
        geocode.parse_exact_address(exact_address_regex, original)
    eq_(method, 'google')
    eq_(search_term.split(' ontario')[0], result)
    eq_(expected_type, geocode.ADDRESS_TYPE)


@parameterized([
    ('1904 fire ruins, n.w. corner of Bay Street and Wellington Street West',
     ('Bay Street', 'Wellington Street West')),
    ('House of Demo - view of southeast corner of building at Sherbourne and Esplanade',
     ('Sherbourne', 'Esplanade')),
    ('Norseman & Development Ltd, 1304 Woodbine Avenue, at Holborne Avenue, south-west corner',
     ('Woodbine Avenue', 'Holborne Avenue')),
    ('Grocery, 391 Brock Avenue, 389 Brock Avenue, at Muir Avenue, southeast corner',
     ('Brock Avenue', 'Muir Avenue')),
    ('Former corner store, 857 and 859 Lansdowne Avenue, north of Wallace Avenue', None),
    ('NE corner Gerrard and River', ('Gerrard', 'River')),
    ('Northeast corner of St. Clair Avenue and McRoberts Avenue',
     ('St. Clair Avenue', 'McRoberts Avenue')),
    ('Three eggs, large, small & long, south-east corner', None),
    ('Demolition of a building, used by Railway Company and Toronto Railway Company, located on'
     'the northwest corner of Front St. E. and Frederick St', ('Front St. E.', 'Frederick St')),
    ('View of Dundas Street West, north-east corner of Ossington Avenue',
     ('Dundas Street West', 'Ossington Avenue')),
    ('Queen St E at Sumach, southeast corner', ('Queen St E', 'Sumach')),
    ('Northeast corner Bruce and Ossington', ('Bruce', 'Ossington')),
    ('Sidewalk construction, north-east corner of Gould and Yonge', ('Gould', 'Yonge')),
    ('Storm photos, pigeon on eggs, s.e. corner', None),
    ('The British Hotel at the north-east corner of Simcoe and King streets', ('Simcoe', 'King')),
    ('South-west corner of Yonge and Dundas', ('Yonge', 'Dundas')),
    ('Southeast corner, chestnut bud', None),
    ('King St E. at Sackville, southeast corner', ('King St E.', 'Sackville')),
    ('Northeast corner of King and Bay streets', ('King', 'Bay')),
    ('Former East York Shoe Repair, 232 Sammon Avenue, at Marlowe Avenue, north-west corner',
     ('Sammon Avenue', 'Marlowe Avenue')),
    ('George Drew, Premier of Ontario, at cornerstone laying for Variety Village', None),
    ('King St E., northeast corner at Princess St', ('King St E.', 'Princess St')),
    ('Northwest corner of Front and Bay', ('Front', 'Bay')),
    ('Southeast corner River and Gerrard', ('River', 'Gerrard')),
    ('Sunkist Fruit Market, north-west corner of Danforth and Carlaw', ('Danforth', 'Carlaw')),
    ('Library addition cornerstone, W. T. J. Lee speaking', None),
    ('Southwest corner Bay and Richmond Cave-in', ('Bay', 'Richmond Cave')),
    ('S. E. corner, double feather', None),
    ('Corner of Sackville St. and St. Paul St., looking south', ('Sackville St.', 'St. Paul St.')),
    ('Corner of Sherbourne St. and Queens Quay, looking north-east',
     ('Sherbourne St.', 'Queens Quay')),
    ('Corner of George St. and Dundas St., looking south-east', ('George St.', 'Dundas St.')),
    ('Corner of Sherbourne St. and the Gardiner Expressway, looking south-west',
     ('Sherbourne St.', 'Gardiner Expressway')),
    ('Corner of University Ave. and Queen\'s Park Cres., looking east',
     ('University Ave.', 'Queen\'s Park Cres.'))
])
def corner_test(original, test):
    result = geocode.parse_corner(original)
    if result:
        method, search_term, parse_result, expected_type = result
        technique, a, b = parse_result
        eq_((a, b), test)
        eq_(geocode.INTERSECTION_TYPE, expected_type)
    else:
        eq_(result, test)


@parameterized([
    ('O’Neills Hall, Queen & Parliament', ('Queen', 'Parliament')),
    ('Apartment buildings, Roselawn Avenue and Chaplin Crescent',
     ('Roselawn Avenue', 'Chaplin Crescent')),
    ('Yonge and Queen looking north', ('Yonge', 'Queen')),
    ('Proposed playground site at Davenport Road, Christie Street, and Benson Avenue',
     ('Christie Street', 'Benson Avenue')),
    ('Bank of Montreal on northeast corner of Queen and Yonge', ('Queen', 'Yonge')),
    ('Plaque on the northeast corner of King and John for hospital',
     ('King', 'John')),
    ('Dufferin Street and Eglinton Avenue', ('Dufferin Street', 'Eglinton Avenue')),
    ('Building at 150 Avenue Road on north-east corner of Bloor and Avenue', ('Bloor', 'Avenue'))
])
def parse_streets_joined_by_and_test(original, expected):
    method, search_term, parse_result, expected_type = \
        geocode.parse_streets_joined_by_and(original)
    technique, one, two = parse_result
    eq_(method, 'google')
    eq_((one, two), expected)
    assert search_term.startswith(f'{one} and {two}'), (
        f'{search_term} does not start with {one}, {two}')
    eq_(geocode.INTERSECTION_TYPE, expected_type)


@parameterized([
    ('King Street', 'King St', True),
    ('King Street West', 'King St', False),
    ('King St. E.', 'King Street East', True)
])
def are_streets_same_test(street1, street2, result):
    eq_(result, geocode.are_streets_same(street1, street2))


@parameterized([
    ([], []),
    (['King Street'], ['King Street']),
    (['King Street', 'Queen Street'], ['King Street', 'Queen Street']),
    (['King Street', 'King St'], ['King Street']),
    (['King Street', 'King St. W.', 'King St.'], ['King Street', 'King St. W.'])
])
def unique_streets_test(streets, result):
    eq_(result, geocode.unique_streets(streets))


def parse_place_name_test():
    pois_file = create_pois_file()
    regex, place_map = geocode.build_place_name_regex(pois_file.name)

    # "C. N. E." should take precedence because of its score, even though it's second in the title.
    eq_(('exact', 'c. n. e.', ('43.633751', '-79.4192546'), ''),
        geocode.parse_place_name(regex, place_map, 'high park enches, c. n. e.'))

    # match for full title
    eq_(('exact', 'high park', ('43.6462345', '-79.4627137'), ''),
        geocode.parse_place_name(regex, place_map, 'high park'))

    # "CNE" is special-cased as a short but valid POI.
    eq_(('exact', 'cne', ('43.633751', '-79.4192546'), ''),
        geocode.parse_place_name(regex, place_map, 'high park enches, cne'))


def create_images_ndjson(images):
    images_ndjson = tempfile.NamedTemporaryFile()
    images_ndjson.write(bytes('\n'.join([json.dumps(i) for i in images]), 'utf8'))
    images_ndjson.flush()
    return images_ndjson


def create_street_names_file():
    street_names_file = tempfile.NamedTemporaryFile()
    street_names_file.write(bytes('\n'.join(street_names), 'utf8'))
    street_names_file.flush()
    return street_names_file


def create_pois_file():
    pois_file = tempfile.NamedTemporaryFile()
    pois_file.write(bytes('\n'.join(pois), 'utf8'))
    pois_file.flush()
    return pois_file


def check_output_file(output_file):
    output_file.flush()
    output_file.seek(0)
    as_json = json.load(output_file)
    ok_('100022' not in as_json)
    eq_(as_json['100001']['original_title'], 'Rear of 203 Church Street leaning wall')
    eq_(as_json['100001']['lng'], -79.3766057)
    eq_(as_json['100004']['original_title'], '161 Beatrice Street')
    eq_(as_json['100007']['original_title'], 'Northwest corner Davenport Road and Uxbridge Avenue'
        ' - Defective building')
    eq_(as_json['100007']['lat'], 43.6701965)

    eq_(as_json['100023'], {
        'original_title': 'C. N. E. - Grandstand',
        'lat': 43.633751,
        'lng': -79.4192546,
        'search_term': 'c. n. e.',
        'technique': ['POI', 'c. n. e.']
    })

    eq_(as_json['100024'], {
        'original_title': 'High Park benches',
        'lat': 43.6462345,
        'lng': -79.4627137,
        'search_term': 'high park',
        'technique': ['POI', 'high park']
    })


def geocode_pipeline_test():
    images_ndjson = create_images_ndjson(images)
    street_names_file = create_street_names_file()
    pois_file = create_pois_file()
    output_file = tempfile.NamedTemporaryFile()
    maps_client = MapsClientMock()
    geocode.main(
        images_ndjson.name, street_names_file.name, pois_file.name,
        output_file.name, 1.0, None, maps_client, False)
    check_output_file(output_file)
