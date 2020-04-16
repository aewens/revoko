#!/usr/bin/env python3

from revoko.daemon import entry

from argparse import ArgumentParser, FileType

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-c", "--config", dest="config", type=FileType("r"),
        required=True)

    parser.add_argument("-t", "--timeout", dest="timeout", nargs="?", type=int,
        default=3 * 60)

    args = parser.parse_args()
    entry(args.config)
