import argparse

from ebmlite.tools import utils
import ebmlite.util


def main():
    argparser = argparse.ArgumentParser(
        description="A tool for converting xml to ebml."
    )
    argparser.add_argument(
        'input', metavar="FILE.xml", help="The source XML file.",
    )
    argparser.add_argument(
        'schema',
        metavar="SCHEMA.xml",
        help=(
          "The name of the schema file. Only the name itself is required if"
          " the schema file is in the standard schema directory."
        ),
    )
    argparser.add_argument(
        '-o', '--output', metavar="FILE.ebml", help="The output file.",
    )
    argparser.add_argument(
        '-c', '--clobber', action="store_true",
        help="Clobber (overwrite) existing files.",
    )
    args = argparser.parse_args()

    with utils.load_files(args, binary_output=True) as (schema, out):
        ebmlite.util.xml2ebml(args.input, out, schema)  # , sizeLength=4, headers=True, unknown=True)


if __name__ == "__main__":
    main()
