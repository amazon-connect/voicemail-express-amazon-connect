"""
A tool for listing all EBML schemata in SCHEMA_PATH, including paths in the
EBMLITE_SCHEMA_PATH (if present), and (optionally) any additional paths
specified by the user. Additional paths may include module names enclosed in
braces (e.g., "{idelib}").
"""

import argparse
import sys

import ebmlite.util
import ebmlite.core


def main():
    argparser = argparse.ArgumentParser(description=__doc__.strip())

    argparser.add_argument(
        '-o', '--output', metavar="FILE.txt", help="An optional output file",
        default=sys.stdout
    )
    argparser.add_argument(
        '-r', '--relative', action="store_true",
        help="Show schema filenames with package-relative path references",
    )
    argparser.add_argument(
        'paths', nargs='*',
        help="Additional paths to search for schemata; will be searched before paths in SCHEMA_PATH"
    )

    args = argparser.parse_args()
    ebmlite.util.printSchemata(paths=args.paths, out=args.output, absolute=not args.relative)


if __name__ == "__main__":
    main()

