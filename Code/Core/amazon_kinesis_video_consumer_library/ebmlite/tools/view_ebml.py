import argparse

from ebmlite.tools import utils
import ebmlite.util
import ebmlite.xml_codecs


def main():
    # Build help text listing the binary codecs, and get the default one.
    codecs = list(ebmlite.xml_codecs.BINARY_CODECS)
    default_codec = "ignore"
    codec_desc = ""
    for name, codec in ebmlite.xml_codecs.BINARY_CODECS.items():
        name = '"{}"'.format(name)
        if codec.NAME == default_codec:
            name += ' (default)'.format(name)
        codec_desc += '{}: {}\n'.format(name, " ".join(codec.__doc__.split()))

    argparser = argparse.ArgumentParser(
        description="A tool for reading ebml file content."
    )
    argparser.add_argument(
        'input', metavar="FILE.ebml", help="The source XML file.",
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
        '-o', '--output', metavar="FILE.xml", help="The output file.",
    )
    argparser.add_argument(
        '-c', '--clobber', action="store_true",
        help="Clobber (overwrite) existing files.",
    )
    argparser.add_argument(
        '-e', '--encoding',
        choices=codecs,
        default=default_codec,
        help="The method of encoding binary data as text.\n" + codec_desc
    )

    args = argparser.parse_args()

    codec = ebmlite.xml_codecs.BINARY_CODECS[args.encoding.strip().lower()]()

    with utils.load_files(args, binary_output=False) as (schema, out):
        doc = schema.load(args.input, headers=True)
        ebmlite.util.pprint(doc, out=out, binary_codec=codec)


if __name__ == "__main__":
    main()
