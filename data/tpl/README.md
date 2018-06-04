# Toronto Public Library (TPL) images

These images come from the TPL Digital Collections.

For example,
https://www.torontopubliclibrary.ca/detail.jsp?Entt=RDMDC-964-6-43&R=DC-964-6-43

becomes:

```json
{
  "title": "Cayuga (1907-1960), leaving Toronto through Eastern Gap ",
  "title_alt": null,
  "url": "http://www.torontopubliclibrary.ca:80/detail.jsp?Entt=RDMDC-964-6-43&R=DC-964-6-43",
  "uniqueID": "DC-964-6-43",
  "creator": "Williams, Charles A., fl. 1897-1962",
  "license": "Toronto Public Library",
  "access": "Public Domain",
  "provenance": null,
  "date": "1918-07?",
  "subject": "Cayuga (Steamer : 1907-1960)\nEastern Gap (Toronto Harbour, Ont.)\nFactories--Ontario--Toronto\nWilliams, Charles A.--Portraits",
  "location": null,
  "description": "MAY 24 1989\nPerhaps includes Williams' daughters.\nTEC 1119.5B",
  "rights_holder": null,
  "imageLink": "https://static.torontopubliclibrary.ca/da/images/MC/964-6-43.jpg"
}
```

in `data/tpl/toronto-library.ndjson`.

This data was assembled by doing an empty search and parsing the results in XML format.
See `oldtoronto/parse_library_xml.py` and `data/tpl/tpl-rss-urls.txt`.
