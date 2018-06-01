import collections


def deep_update(d, u):
    """Do a deep, in-place update of d with u."""
    # See https://stackoverflow.com/a/3233356/388951
    for k, v in u.items():
        if isinstance(v, collections.Mapping):
            d[k] = deep_update(d.get(k, {}), v)
        else:
            d[k] = v
    return d
