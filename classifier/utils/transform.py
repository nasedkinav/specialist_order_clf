import re

RE_FLOAT_PATTERN = re.compile('^[^\d]*(\d+\.?\d*)[^\d]*$', re.I | re.U)


def not_empty_str(s):
    return 0 if s is None or isinstance(s, (unicode, str)) and not len(s.strip()) else 1


def to_binary(val):
    return int(bool(val))


def one_hot_encode(val, enum, prefix):
    return {str(prefix) + str(k): int(val == v) for v, k in enum.iteritems()}


def clean_float(n, default=None):
    match = RE_FLOAT_PATTERN.match(str(n) if isinstance(n, (int, long)) else n)
    return float(match.group(1)) if match else default
