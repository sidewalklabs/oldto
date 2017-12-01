"""Utilities for working with the Toronto Archives web site."""

import re

URL_PATTERN = 'https://gencat4.eloquent-systems.com/webcat/request/Action?SystemName=City+of+Toronto+Archives&UserName=wa+public&Password=&TemplateProcessID=6000_3355&PromptID=&ParamID=&TemplateProcessID=6000_1051_1051&PromptID=&ParamID=&CMD_(DetailRequest)[0]=&ProcessID=6000_3363(0)&KeyValues=KEY_%s'  # noqa: E501

# This resolves to URL_PATTERN via a redirect.
SHORT_URL_PATTERN = 'https://gencat.eloquent-systems.com/city-of-toronto-archives-m-permalink.html?key=%s'  # noqa: E501


def url_for_unique_id(unique_id):
    """Get the URL for the mobile page for the given ID.

    This will resolve without redirects.
    The mobile page tends to be easier to work with than the desktop version.
    These pages can be parsed using parse_records.py.
    """
    return URL_PATTERN % unique_id


def split_citation_hierarchy(citation):
    """Split a full citation like 'Fonds 200, Series 123, Item 456' into its parts.

    e.g. 'Fonds 200, Series 123, Item 456' --> ['Fonds 200', 'Series 123', 'Item 456'].
    """
    # One of the citations looks like "Fonds 257, Series 12, File 1983,  52\",\""
    citation = re.sub(r'","', '', citation)
    return citation.split(', ')


def get_citation_hierarchy(citation):
    """Return a list of all the ancestors in a citation's hierarchy.

    Returns most- to least-specific citations, e.g.
    'Fonds 200, Series 123, Item 456'
    --> ['Fonds 200, Series 123', 'Fonds 200']
    """
    series = ''
    parts = split_citation_hierarchy(citation)
    parents = []
    for i, part in enumerate(parts[:-1]):
        if i > 0:
            series += ', '
        series += part
        parents.append(series)
    parents.reverse()
    return parents
