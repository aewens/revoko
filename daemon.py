#!/usr/bin/env python3

from sys import stderr, exit
from json import loads as json_loads
from argparse import ArgumentParser, FileType

# DEBUG
from pprint import pprint

def eprint(*args, **kwargs):
    print(*args, file=stderr, **kwargs)

def main(config_file):
    config_data = config_file.read()
    try:
        config = json_loads(config_data)

    except ValueError as e:
        eprint(e)
        exit(1)

    pprint(config)

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-c", "--config", dest="config", type=FileType("r"),
        required=True)

    args = parser.parse_args()
    main(args.config)
