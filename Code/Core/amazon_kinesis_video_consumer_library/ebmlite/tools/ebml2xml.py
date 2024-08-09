import argparse
from xml.dom.minidom import parseString
from xml.etree import ElementTree as ET

from ebmlite.tools import utils
import ebmlite.util
import ebmlite.xml_codecs


def main():
    # Build help text listing the binary codecs, and get the default one.
    codecs = list(ebmlite.xml_codecs.BINARY_CODECS)
    default_codec = codecs[0]
    codec_desc = ""
    for name, codec in ebmlite.xml_codecs.BINARY_CODECS.items():
        name = '"{}"'.format(name)
        if codec.NAME == default_codec:
            name += ' (default)'.format(name)
        codec_desc += '{}: {}\n'.format(name, " ".join(codec.__doc__.split()))

    argparser = argparse.ArgumentParser(
        description="A tool for converting ebml to xml."
    )
    argparser.add_argument(
        'input', metavar="FILE.ebml", help="The source EBML file.",
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
        '-s', '--single', action="store_true", help="Generate XML as a single line with no newlines or indents",
    )
    argparser.add_argument(
        '-m', '--max',
        action="store_true",
        help="Generate XML with maximum description, including offset, size, type, and id info",
    )
    argparser.add_argument(
        '-e', '--encoding',
        choices=codecs,
        default=default_codec,
        help="The method of encoding binary data as text.\n" + codec_desc
    )

    args = argparser.parse_args()

    codecargs = {'cols': None} if args.single else {}
    codec = ebmlite.xml_codecs.BINARY_CODECS[args.encoding.strip().lower()](**codecargs)

    with utils.load_files(args, binary_output=args.single) as (schema, out):
        doc = schema.load(args.input, headers=True)
        if args.max:
            root = ebmlite.util.toXml(doc, offsets=True, sizes=True, types=True, ids=True, binary_codec=codec)
        else:
            root = ebmlite.util.toXml(doc, offsets=False, sizes=False, types=False, ids=False, binary_codec=codec)
        s = ET.tostring(root, encoding="utf-8")
        if args.single:
            out.write(s)
        else:
            parseString(s).writexml(out, addindent='\t', newl='\n', encoding='utf-8')


if __name__ == "__main__":
    main()
