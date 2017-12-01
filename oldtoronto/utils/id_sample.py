"""Tools for sampling IDs in a deterministic way."""

from zlib import crc32


# See https://stackoverflow.com/a/42909410/388951
def _bytes_to_float(b):
    return float(crc32(b) & 0xffffffff) / 2 ** 32


def _str_to_float(s, encoding='utf-8'):
    return _bytes_to_float(s.encode(encoding))


def should_sample(id_, sampling_rate):
    return _str_to_float(id_) <= sampling_rate
