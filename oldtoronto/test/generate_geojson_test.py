from io import StringIO

import sys

sys.path.append('oldtoronto')
from oldtoronto.generate_geojson import load_patch_csv # noqa


TEST_DATA = StringIO("""Timestamp,Photo Id,Location suggestion,Lat,Lng,Fixed
3/20/2018 16:08:52,449487,"This is from Toronto Island, not downtown.",,,Yes
3/20/2018 16:17:46,144582,Wrong location. No history of railway here.,10,10,
3/20/2018 16:29:48,212373,This is on Eastwood Rd near Bowmore Rd.,,,
3/20/2018 17:48:30,462670,This is nowhere near King. ,,,
3/20/2018 16:29:48,212373,This is on Eastwood Rd near Bowmore Rd.,,,""")


def test_load_patch_csv():
    patched = load_patch_csv(TEST_DATA)
    assert patched['212373'] is None
    assert patched['144582'] == (10, 10)
    assert '462670' not in patched
