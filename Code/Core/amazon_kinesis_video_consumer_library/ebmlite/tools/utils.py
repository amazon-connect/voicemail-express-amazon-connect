import contextlib
import sys
import os.path

from ebmlite import core


def errPrint(msg):
    sys.stderr.write("%s\n" % msg)
    sys.stderr.flush()
    exit(1)


@contextlib.contextmanager
def load_files(args, binary_output=False):
    if not os.path.exists(args.input):
        sys.stderr.write("Input file does not exist: %s\n" % args.input)
        exit(1)

    try:
        schema_file = args.schema
        if os.path.splitext(schema_file.strip())[1] == '':
            schema_file += '.xml'
        schema = core.loadSchema(schema_file)
    except IOError as err:
        errPrint("Error loading schema: %s\n" % err)

    if not args.output:
        yield (schema, sys.stdout)
        return

    output = os.path.realpath(os.path.expanduser(args.output))
    if os.path.exists(output) and not args.clobber:
        errPrint("Error: Output file already exists: %s" % args.output)
    with open(output, ('wb' if binary_output else 'w')) as out:
        yield (schema, out)
