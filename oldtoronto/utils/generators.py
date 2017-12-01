import json


def read_ndjson_file(input_file):
    return (json.loads(line) for line in open(input_file))
