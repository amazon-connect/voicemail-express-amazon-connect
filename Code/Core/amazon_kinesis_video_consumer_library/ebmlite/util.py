"""
Some utilities for manipulating EBML documents: translate to/from XML, etc.
This module may be imported or used as a command-line utility.

Created on Aug 11, 2017

@todo: Clean up and standardize usage of the term 'size' versus 'length.'
@todo: Modify (or create an alternate version of) `toXml()` that writes
    directly to a file, allowing the conversion of huge EBML files.
@todo: Add other options to command-line utility for the other arguments of
    `toXml()` and `xml2ebml()`.
"""
__author__ = "David Randall Stokes, Connor Flanigan"
__copyright__ = "Copyright 2021, Mide Technology Corporation"
__credits__ = "David Randall Stokes, Connor Flanigan, Becker Awqatty, Derek Witt"

__all__ = ['createID', 'validateID', 'toXml', 'xml2ebml', 'loadXml', 'pprint',
           'printSchemata']

import ast
from base64 import b64encode, b64decode
from io import StringIO
import pathlib
import struct
import sys
import tempfile
from xml.etree import ElementTree as ET

from . import core, encoding, decoding
from . import xml_codecs

# ==============================================================================
#
# ==============================================================================


def createID(schema, idClass, exclude=(), minId=0x81, maxId=0x1FFFFFFE, count=1):
    """ Generate unique EBML IDs. Primarily intended for use 'offline' by
        humans creating EBML schemata.

        @param schema: The `Schema` in which the new IDs must coexist.
        @param idClass: The EBML class of ID, one of (case-insensitive):
            * `'a'`: Class A (1 octet, base 0x8X)
            * `'b'`: Class B (2 octets, base 0x4000)
            * `'c'`: Class C (3 octets, base 0x200000)
            * `'d'`: Class D (4 octets, base 0x10000000)
        @param exclude: A list of additional IDs to avoid.
        @param minId: The minimum ID value, within the ID class' range.
        @param maxId: The maximum ID value, within the ID class' range.
        @param count: The maximum number of IDs to generate. The result may be
            fewer than specified if too few meet the given criteria.
        @return: A list of EBML IDs that match the given criteria.
    """
    ranges = dict(A=(0x81, 0xFE),
                  B=(0x407F, 0x7FFE),
                  C=(0x203FFF, 0x3FFFFE),
                  D=(0x101FFFFF, 0x1FFFFFFE))
    idc = idClass.upper()
    if idc not in ranges:
        raise KeyError('Invalid ID class %r: must be one of %r' %
                       (idClass, list(ranges)))

    # Keep range within the one specified and the one imposed by the ID class
    idrange = (max(ranges[idc][0], minId),
               min(ranges[idc][1], maxId))

    exclude = set(exclude).union(schema.elements.keys())

    result = []
    for i in (x for x in range(*idrange) if x not in exclude):
        if len(result) == count:
            break
        result.append(i)

    return result


def validateID(elementId):
    """ Verify that a number is a valid EBML element ID. A `ValueError`
        will be raised if the element ID is invalid.

        Valid ranges for the four classes of EBML ID are:
          * A: 0x81 to 0xFE
          * B: 0x407F to 0x7FFE
          * C: 0x203FFF to 0x3FFFFE
          * D: 0x101FFFFF to 0x1FFFFFFE

        @param elementId: The element ID to validate
        @raises: `ValueError`, although certain edge cases may raise
            another type.
    """
    ranges = ((0x81, 0xFE), (0x407F, 0x7FFE), (0x203FFF, 0x3FFFFE), (0x101FFFFF, 0x1FFFFFFE))

    msg = "Invalid element ID"  # Default error message

    # Basic check: is the ID within the bounds of the total ID range?
    if not 0x81 <= elementId <= 0x1FFFFFFE:
        raise ValueError("Element ID out of range", elementId)

    try:
        # See if the first byte properly encodes the length of the ID.
        s = struct.pack(">I", elementId).lstrip(b'\x00')
        length, _ = decoding.decodeIDLength(s[0])
        valid = len(s) == length  # Should always be True if decoding worked
        if valid:
            minId, maxId = ranges[length-1]
            if not minId <= elementId <= maxId:
                msg = "ID out of range for class %s %s" % (" ABCD"[length], ranges[length-1])
                valid = False

    # Note: Change this if decoding changes the exceptions it raises
    except OSError as err:
        valid = False
        msg = err.args[0] if err.args else msg

    if not valid:
        raise ValueError(msg, elementId)
    
    return True

# ==============================================================================
#
# ==============================================================================


def toXml(el, parent=None, offsets=True, sizes=True, types=True, ids=True,
          binary_codec='base64', void_codec='ignore'):
    """ Convert an EBML Document to XML. Binary elements will contain
        base64-encoded data in their body. Other non-master elements will
        contain their value in a ``value`` attribute.

        @param el: An instance of an EBML Element or Document subclass.
        @keyword parent: The resulting XML element's parent element, if any.
        @keyword offsets: If `True`, create a ``offset`` attributes for each
            generated XML element, containing the corresponding EBML element's
            offset.
        @keyword sizes: If `True`, create ``size`` attributes containing the
            corresponding EBML element's size.
        @keyword types: If `True`, create ``type`` attributes containing the
            name of the corresponding EBML element type.
        @keyword ids: If `True`, create ``id`` attributes containing the
            corresponding EBML element's EBML ID.
        @keyword binary_codec: The name of an XML codec class from
            `ebmlite.xml_codecs`, or an instance of a codec, for rendering
            binary elements as text.
        @keyword void_codec:  The name of an XML codec class from
            `ebmlite.xml_codecs`, or an instance of a codec, for rendering
            the contents of Void elements as text.
        @return The root XML element of the file.
    """
    if isinstance(binary_codec, str):
        binary_codec = xml_codecs.BINARY_CODECS[binary_codec]()
    if isinstance(void_codec, str):
        void_codec = xml_codecs.BINARY_CODECS[void_codec]()

    if isinstance(el, core.Document):
        elname = el.__class__.__name__
    else:
        elname = el.name

    if parent is None:
        xmlEl = ET.Element(elname)
    else:
        xmlEl = ET.SubElement(parent, elname)
    if isinstance(el, core.Document):
        xmlEl.set('source', el.filename)
        xmlEl.set('schemaName', el.schema.name)
        xmlEl.set('schemaFile', el.schema.filename)
    else:
        if ids and isinstance(el.id, int):
            xmlEl.set('id', "0x%X" % el.id)
        if types:
            xmlEl.set('type', el.dtype.__name__)

    if offsets:
        xmlEl.set('offset', str(el.offset))
    if sizes:
        xmlEl.set('size', str(el.size))

    if isinstance(el, core.MasterElement):
        for chEl in el:
            toXml(chEl, xmlEl, offsets, sizes, types, ids, binary_codec, void_codec)
    elif isinstance(el, core.VoidElement):
        xmlEl.set('size', str(el.size))
        if void_codec.NAME != 'ignore':
            xmlEl.set('encoding', void_codec.NAME)
        xmlEl.text = void_codec.encode(el.value)
    elif isinstance(el, core.BinaryElement):
        xmlEl.set('encoding', binary_codec.NAME)
        xmlEl.text = binary_codec.encode(el.value, offset=el.offset)
    elif not isinstance(el, core.VoidElement):
        xmlEl.set('value', str(el.value).encode('ascii', 'xmlcharrefreplace').decode())

    return xmlEl


#===============================================================================
#
#===============================================================================

def xmlElement2ebml(xmlEl, ebmlFile, schema, sizeLength=None, unknown=True):
    """ Convert an XML element to EBML, recursing if necessary. For converting
        an entire XML document, use `xml2ebml()`.

        @param xmlEl: The XML element. Its tag must match an element defined
            in the `schema`.
        @param ebmlFile: An open file-like stream, to which the EBML data will
            be written.
        @param schema: An `ebmlite.core.Schema` instance to use when
            writing the EBML document.
        @keyword sizeLength:
        @param unknown: If `True`, unknown element names will be allowed,
            provided their XML elements include an ``id`` attribute with the
            EBML ID (in hexadecimal).
        @return The length of the encoded element, including header and children.
        @raise NameError: raised if an xml element is not present in the schema and unknown is False, OR if the xml
            element does not have an ID.
    """
    if not isinstance(xmlEl.tag, (str, bytes, bytearray)):
        # (Probably) a comment; disregard.
        return 0

    try:
        cls = schema[xmlEl.tag]
        encId = encoding.encodeId(cls.id)
    except (KeyError, AttributeError):
        # Element name not in schema. Go ahead if allowed (`unknown` is `True`)
        # and the XML element specifies an ID,
        if not unknown:
            raise NameError("Unrecognized EBML element name: %s" % xmlEl.tag)

        eid = xmlEl.get('id', None)
        if eid is None:
            raise NameError("Unrecognized EBML element name with no 'id' "
                            "attribute in XML: %s" % xmlEl.tag)
        cls = core.UnknownElement
        encId = encoding.encodeId(int(eid, 16))
        cls.id = int(eid, 16)

    codec = xmlEl.get('encoding', 'base64')

    if sizeLength is None:
        sl = xmlEl.get('sizeLength', None)
        if sl is None:
            s = xmlEl.get('size', None)
            if s is not None:
                sl = encoding.getLength(int(s))
            else:
                sl = 4
        else:
            sl = int(sl)
    else:
        sl = xmlEl.get('sizeLength', sizeLength)

    if issubclass(cls, core.MasterElement):
        ebmlFile.write(encId)
        sizePos = ebmlFile.tell()
        ebmlFile.write(encoding.encodeSize(None, sl))
        size = 0
        for chEl in xmlEl:
            size += xmlElement2ebml(chEl, ebmlFile, schema, sl)
        endPos = ebmlFile.tell()
        ebmlFile.seek(sizePos)
        ebmlFile.write(encoding.encodeSize(size, sl))
        ebmlFile.seek(endPos)
        return len(encId) + (endPos - sizePos)

    elif issubclass(cls, core.BinaryElement):
        val = xml_codecs.BINARY_CODECS[codec].decode(xmlEl.text)
    elif issubclass(cls, (core.IntegerElement, core.FloatElement)):
        val = ast.literal_eval(xmlEl.get('value'))
    else:
        val = cls.dtype(xmlEl.get('value'))

    size = xmlEl.get('size', None)
    if size is not None:
        size = int(size)
    sl = xmlEl.get('sizeLength')
    if sl is not None:
        sl = int(sl)

    encoded = cls.encode(val, size, lengthSize=sl)
    ebmlFile.write(encoded)
    return len(encoded)


def xml2ebml(xmlFile, ebmlFile, schema, sizeLength=None, headers=True,
             unknown=True):
    """ Convert an XML file to EBML.

        @todo: Convert XML on the fly, rather than parsing it first, allowing
            for the conversion of arbitrarily huge files.

        @param xmlFile: The XML source. Can be a filename, an open file-like
            stream, or a parsed XML document.
        @param ebmlFile: The EBML file to write. Can be a filename or an open
            file-like stream.
        @param schema: The EBML schema to use. Can be a filename or an
            instance of a `Schema`.
        @keyword sizeLength: The default length of each element's size
            descriptor. Must be large enough to store the largest 'master'
            element. If an XML element has a ``sizeLength`` attribute, it will
            override this.
        @keyword headers: If `True`, generate the standard ``EBML`` EBML
            element if the XML document does not contain one.
        @param unknown: If `True`, unknown element names will be allowed,
            provided their XML elements include an ``id`` attribute with the
            EBML ID (in hexadecimal).
        @return: the size of the ebml file in bytes.
        @raise NameError: raises if an xml element is not present in the schema.
    """
    if isinstance(ebmlFile, (str, bytes, bytearray)):
        ebmlFile = open(ebmlFile, 'wb')
        openedEbml = True
    else:
        openedEbml = False

    if not isinstance(schema, core.Schema):
        schema = core.loadSchema(schema)

    if isinstance(xmlFile, ET.Element):
        # Already a parsed XML element
        xmlRoot = xmlFile
    elif isinstance(xmlFile, ET.ElementTree):
        # Already a parsed XML document
        xmlRoot = xmlFile.getroot()
    else:
        xmlDoc = ET.parse(xmlFile)
        xmlRoot = xmlDoc.getroot()

    if xmlRoot.tag not in schema and xmlRoot.tag != schema.document.__name__:
        raise NameError("XML element %s not an element or document in "
                        "schema %s (wrong schema)" % (xmlRoot.tag, schema.name))

    headers = headers and 'EBML' in schema
    if headers and 'EBML' not in (el.tag for el in xmlRoot):
        pos = ebmlFile.tell()
        cls = schema.document
        ebmlFile.write(cls.encodePayload(cls._createHeaders()))
        numBytes = ebmlFile.tell() - pos
    else:
        numBytes = 0

    if xmlRoot.tag == schema.document.__name__:
        for el in xmlRoot:
            numBytes += xmlElement2ebml(el, ebmlFile, schema, sizeLength,
                                        unknown=unknown)
    else:
        numBytes += xmlElement2ebml(xmlRoot, ebmlFile, schema, sizeLength,
                                    unknown=unknown)

    if openedEbml:
        ebmlFile.close()

    return numBytes

#===============================================================================
#
#===============================================================================


def loadXml(xmlFile, schema, ebmlFile=None):
    """ Helpful utility to load an EBML document from an XML file.

        @param xmlFile: The XML source. Can be a filename, an open file-like
            stream, or a parsed XML document.
        @param schema: The EBML schema to use. Can be a filename or an
            instance of a `Schema`.
        @keyword ebmlFile: The name of the temporary EBML file to write, or
            ``:memory:`` to use RAM (like `sqlite3`). Defaults to an
            automatically-generated temporary file.
        @return The root node of the specified EBML file.
    """
    if ebmlFile == ":memory:":
        ebmlFile = StringIO()
        xml2ebml(xmlFile, ebmlFile, schema)
        ebmlFile.seek(0)
    else:
        ebmlFile = tempfile.mktemp() if ebmlFile is None else ebmlFile
        xml2ebml(xmlFile, ebmlFile, schema)

    return schema.load(ebmlFile)


#===============================================================================
#
#===============================================================================

def pprint(el, values=True, out=sys.stdout, indent="  ", binary_codec="ignore",
           void_codec="ignore", _depth=0):
    """ Test function to recursively crawl an EBML document or element and
        print its structure, with child elements shown indented.

        @param el: An instance of a `Document` or `Element` subclass.
        @keyword values: If `True`, show elements' values.
        @keyword out: A file-like stream to which to write.
        @keyword indent: The string containing the character(s) used for each
            indentation.
        @keyword binary_codec: The name of a class from `ebmlite.xml_codecs`,
            or an instance of a codec, for rendering binary elements as text.
        @keyword void_codec: The name of a class from `ebmlite.xml_codecs`,
            or an instance of a codec, for rendering the contents of Void
            elements as text.
    """
    tab = indent * _depth

    if isinstance(binary_codec, str):
        binary_codec = xml_codecs.BINARY_CODECS[binary_codec]()
    if isinstance(void_codec, str):
        void_codec = xml_codecs.BINARY_CODECS[void_codec]()

    if _depth == 0:
        if values:
            out.write("Offset Size   Element (ID): Value\n")
        else:
            out.write("Offset Size   Element (ID)\n")
        out.write("====== ====== =================================\n")

    if isinstance(el, core.Document):
        out.write("%06s %06s %s %s (Document, type %s)\n" % (el.offset, el.size, tab, el.name, el.type))
        for i in el:
            pprint(i, values, out, indent, binary_codec, void_codec, _depth+1)
    else:
        out.write("%06s %06s %s %s (ID 0x%0X)" % (el.offset, el.size, tab, el.name, el.id))
        if isinstance(el, core.MasterElement):
            out.write(": (master) %d subelements\n" % len(el.value))
            for i in el:
                pprint(i, values, out, indent, binary_codec, void_codec, _depth+1)
        else:
            out.write(": (%s)" % el.dtype.__name__)
            if values:
                if isinstance(el, core.BinaryElement):
                    indent = tab + " " * 17
                    if isinstance(el, core.VoidElement) and void_codec.NAME != 'ignore':
                        out.write(" <{}>".format(void_codec.NAME))
                        void_codec.encode(el.value, offset=el.offset, indent=indent, stream=out)
                    elif binary_codec.NAME != 'ignore':
                        out.write(" <{}>".format(binary_codec.NAME))
                        binary_codec.encode(el.value, offset=el.offset, indent=indent, stream=out)
                else:
                    out.write(" %r" % (el.value))
            out.write("\n")

    out.flush()


#===============================================================================
#
#===============================================================================

def printSchemata(paths=None, out=sys.stdout, absolute=True):
    """ Display a list of schemata in `SCHEMA_PATH`. A thin wrapper for the
        core `listSchemata()` function.

        @param out: A file-like stream to which to write.
    """
    out = out or sys.stdout
    newfile = isinstance(out, (str, pathlib.Path))
    if newfile:
        out = open(out, 'w')

    try:
        if paths:
            paths.extend(core.SCHEMA_PATH)
        else:
            paths = core.SCHEMA_PATH
        schemata = core.listSchemata(*paths, absolute=absolute)
        for k, v in schemata.items():
            out.write("{}\n".format(k))
            for s in v:
                out.write("    {}\n".format(s))
        out.flush()
    finally:
        if newfile:
            out.close()
