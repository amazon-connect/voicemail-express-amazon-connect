"""
Functions for decoding EBML elements and their values.

Note: this module does not decode `Document`, `BinaryElement`, or
`MasterElement` objects; these are handled entirely in `core.py`. `Document`
and `MasterElement` objects are special cases, and `BinaryElement` objects do
not require special decoding. 
"""
__author__ = "David Randall Stokes, Connor Flanigan"
__copyright__ = "Copyright 2021, Mide Technology Corporation"
__credits__ = "David Randall Stokes, Connor Flanigan, Becker Awqatty, Derek Witt"

__all__ = ['readElementID', 'readElementSize', 'readFloat', 'readInt',
           'readUInt', 'readDate', 'readString', 'readUnicode']

from datetime import datetime, timedelta
import struct
import warnings

# ==============================================================================
#
# ==============================================================================

# Pre-built structs for packing/unpacking various data types
_struct_uint32 = struct.Struct(">I")
_struct_uint64 = struct.Struct(">Q")
_struct_int64 = struct.Struct(">q")
_struct_float32 = struct.Struct(">f")
_struct_float64 = struct.Struct(">d")

# Direct references to struct methods. Makes things a marginally faster.
_struct_uint32_unpack = _struct_uint32.unpack
_struct_uint64_unpack = _struct_uint64.unpack
_struct_int64_unpack = _struct_int64.unpack
_struct_uint64_unpack_from = _struct_uint64.unpack_from
_struct_int64_unpack_from = _struct_int64.unpack_from
_struct_float32_unpack = _struct_float32.unpack
_struct_float64_unpack = _struct_float64.unpack


# ==============================================================================
# --- Reading and Decoding
# ==============================================================================

def decodeIntLength(byte):
    """ Extract the encoded size from an initial byte.

        @return: The size, and the byte with the size removed (it is the first
            byte of the value).
    """
    # An inelegant implementation, but it's fast.
    if byte >= 128:
        return 1, byte & 0b1111111
    elif byte >= 64:
        return 2, byte & 0b111111
    elif byte >= 32:
        return 3, byte & 0b11111
    elif byte >= 16:
        return 4, byte & 0b1111
    elif byte >= 8:
        return 5, byte & 0b111
    elif byte >= 4:
        return 6, byte & 0b11
    elif byte >= 2:
        return 7, byte & 0b1

    return 8, 0


def decodeIDLength(byte):
    """ Extract the encoded ID size from an initial byte.

        @return: The size and the original byte (it is part of the ID).
        @raise IOError: raise if the length of an ID is invalid.
    """
    if byte >= 128:
        return 1, byte
    elif byte >= 64:
        return 2, byte
    elif byte >= 32:
        return 3, byte
    elif byte >= 16:
        return 4, byte

    length, _ = decodeIntLength(byte)
    raise IOError('Invalid length for ID: %d' % length)


def readElementID(stream):
    """ Read an element ID from a file (or file-like stream).

        @param stream: The source file-like object.
        @return: The decoded element ID and its length in bytes.
        @raise IOError: raised if the length of the ID of an element is greater than 4 bytes.
    """
    ch = stream.read(1)
    length, eid = decodeIDLength(ord(ch))

    if length > 4:
        raise IOError('Cannot decode element ID with length > 4.')
    if length > 1:
        eid = _struct_uint32_unpack((ch + stream.read(length-1)
                                     ).rjust(4, b'\x00'))[0]
    return eid, length


def readElementSize(stream):
    """ Read an element size from a file (or file-like stream).

        @param stream: The source file-like object.
        @return: The decoded size (or `None`) and the length of the
            descriptor in bytes.
    """
    ch = stream.read(1)
    length, size = decodeIntLength(ord(ch))

    if length > 1:
        size = _struct_uint64_unpack((chr(size).encode('latin-1') +
                                      stream.read(length - 1)
                                      ).rjust(8, b'\x00'))[0]

    if size == (2**(7*length)) - 1:
        # EBML 'unknown' size, all bytes 0xFF
        size = None

    return size, length


def readUInt(stream, size):
    """ Read an unsigned integer from a file (or file-like stream).

        @param stream: The source file-like object.
        @param size: The number of bytes to read from the stream.
        @return: The decoded value.
    """

    if size == 0:
        return 0

    data = stream.read(size)
    return _struct_uint64_unpack_from(data.rjust(8, b'\x00'))[0]


def readInt(stream, size):
    """ Read a signed integer from a file (or file-like stream).

        @param stream: The source file-like object.
        @param size: The number of bytes to read from the stream.
        @return: The decoded value.
    """

    if size == 0:
        return 0

    data = stream.read(size)
    if data[0] & 0b10000000:
        pad = b'\xff'
    else:
        pad = b'\x00'
    return _struct_int64_unpack_from(data.rjust(8, pad))[0]


def readFloat(stream, size):
    """ Read an floating point value from a file (or file-like stream).

        @param stream: The source file-like object.
        @param size: The number of bytes to read from the stream.
        @return: The decoded value.
        @raise IOError: raised if the length of this floating point number is not
            valid (0, 4, 8 bytes)
    """
    if size == 4:
        return _struct_float32_unpack(stream.read(size))[0]
    elif size == 8:
        return _struct_float64_unpack(stream.read(size))[0]
    elif size == 0:
        return 0.0

    raise IOError("Cannot read floating point value of length %s; "
                  "only lengths of 0, 4, or 8 bytes supported." % size)


def readString(stream, size):
    """ Read an ASCII string from a file (or file-like stream).

        @param stream: The source file-like object.
        @param size: The number of bytes to read from the stream.
        @return: The decoded value.
    """
    if size == 0:
        return u''

    value = stream.read(size)
    value = value.partition(b'\x00')[0]

    try:
        return str(value, 'ascii')
    except UnicodeDecodeError as ex:
        warnings.warn(str(ex), UnicodeWarning)
        return str(value, 'ascii', 'replace')


def readUnicode(stream, size):
    """ Read an UTF-8 encoded string from a file (or file-like stream).

        @param stream: The source file-like object.
        @param size: The number of bytes to read from the stream.
        @return: The decoded value.
    """

    if size == 0:
        return u''

    data = stream.read(size)
    data = data.partition(b'\x00')[0]
    return str(data, 'utf_8')


def readDate(stream, size=8):
    """ Read an EBML encoded date (nanoseconds since UTC 2001-01-01T00:00:00)
        from a file (or file-like stream).

        @param stream: The source file-like object.
        @param size: The number of bytes to read from the stream.
        @return: The decoded value (as `datetime.datetime`).
        @raise IOError: raised if the length of the date is not 8 bytes.
    """
    if size != 8:
        raise IOError("Cannot read date value of length %d, only 8." % size)
    data = stream.read(size)
    nanoseconds = _struct_int64_unpack(data)[0]
    delta = timedelta(microseconds=(nanoseconds // 1000))
    return datetime(2001, 1, 1, tzinfo=None) + delta
