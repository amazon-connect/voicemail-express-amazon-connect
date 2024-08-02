"""
Functions for encoding EBML elements and their values.

Note: this module does not encode Document or MasterElement objects; they are
special cases, handled in `core.py`.
"""
__author__ = "David Randall Stokes, Connor Flanigan"
__copyright__ = "Copyright 2021, Mide Technology Corporation"
__credits__ = "David Randall Stokes, Connor Flanigan, Becker Awqatty, Derek Witt"

__all__ = ['encodeBinary', 'encodeDate', 'encodeFloat', 'encodeId', 'encodeInt',
           'encodeSize', 'encodeString', 'encodeUInt', 'encodeUnicode']

import datetime
import sys
import warnings

from .decoding import _struct_uint64, _struct_int64
from .decoding import _struct_float32, _struct_float64

# ==============================================================================
#
# ==============================================================================

# If no length is given, use the platform's size of a float.
DEFAULT_FLOAT_SIZE = 4 if sys.maxsize <= 2147483647 else 8

LENGTH_PREFIXES = [0,
                   0x80,
                   0x4000,
                   0x200000,
                   0x10000000,
                   0x0800000000,
                   0x040000000000,
                   0x02000000000000,
                   0x0100000000000000
                   ]

# Translation table for removing invalid EBML string characters (32 < x < 127)
STRING_CHARACTERS = (b"?"*32 + bytearray(range(32, 127))).ljust(256, b'?')

# ==============================================================================
#
# ==============================================================================


def getLength(val):
    """ Calculate the encoded length of a value.
        @param val: A value to be encoded, generally either an ID or a size for
            an EBML element
        @return The minimum length, in bytes, that can be used to represent val
    """
    # Brute force it. Ugly but faster than calculating it.
    if val <= 126:
        return 1
    elif val <= 16382:
        return 2
    elif val <= 2097150:
        return 3
    elif val <= 268435454:
        return 4
    elif val <= 34359738366:
        return 5
    elif val <= 4398046511102:
        return 6
    elif val <= 562949953421310:
        return 7
    else:
        return 8


def encodeSize(val, length=None):
    """ Encode an element size.

        @param val: The size to encode. If `None`, the EBML 'unknown' size
            will be returned (1 or `length` bytes, all bits 1).
        @keyword length: An explicit length for the encoded size. If `None`,
            the size will be encoded at the minimum length required.
        @return: an encoded size for an EBML element.
        @raise ValueError: raised if the length is invalid, or the length cannot
            be encoded.
    """
    if val is None:
        # 'unknown' size: all bits 1.
        length = 1 if (length is None or length == -1) else length
        return b'\xff' * length

    length = getLength(val) if (length is None or length == -1) else length
    try:
        prefix = LENGTH_PREFIXES[length]
        return encodeUInt(val | prefix, length)
    except (IndexError, TypeError):
        raise ValueError("Cannot encode element size %s" % length)


# ==============================================================================
# --- Encoding
# ==============================================================================

def encodeId(eid, length=None):
    """ Encode an element ID.

        @param eid: The EBML ID to encode.
        @keyword length: An explicit length for the encoded data. A `ValueError`
            will be raised if the length is too short to encode the value.
        @return: The binary representation of ID, left-padded with ``0x00`` if
            `length` is not `None`.
        @return: The encoded version of the ID.
        @raise ValueError: raised if length is less than one or more than 4.
    """
    if length is not None:
        if length < 1 or length > 4:
            raise ValueError("Cannot encode an ID 0x%0x to length %d" %
                             (eid, length))
    return encodeUInt(eid, length)


def encodeUInt(val, length=None):
    """ Encode an unsigned integer.

        @param val: The unsigned integer value to encode.
        @keyword length: An explicit length for the encoded data. A `ValueError`
            will be raised if the length is too short to encode the value.
        @return: The binary representation of val as an unsigned integer,
            left-padded with ``0x00`` if `length` is not `None`.
        @raise ValueError: raised if val is longer than length.
    """
    if isinstance(val, float):
        fval, val = val, int(val)
        if fval != val:
            warnings.warn('encodeUInt: float value {} encoded as {}'.format(fval, val))

    pad = b'\x00'
    packed = _struct_uint64.pack(val).lstrip(pad) or pad

    if length is None:
        return packed
    if len(packed) > length:
        raise ValueError("Encoded length (%d) greater than specified length "
                         "(%d)" % (len(packed), length))
    return packed.rjust(length, pad)


def encodeInt(val, length=None):
    """ Encode a signed integer.

        @param val: The signed integer value to encode.
        @keyword length: An explicit length for the encoded data. A `ValueError`
            will be raised if the length is too short to encode the value.
        @return: The binary representation of val as a signed integer,
            left-padded with either ```0x00`` (for positive values) or ``0xFF``
            (for negative) if `length` is not `None`.
        @raise ValueError: raised if val is longer than length.
    """
    if isinstance(val, float):
        fval, val = val, int(val)
        if fval != val:
            warnings.warn('encodeInt: float value {} encoded as {}'.format(fval, val))

    if val >= 0:
        pad = b'\x00'
        packed = _struct_int64.pack(val).lstrip(pad) or pad
        if packed[0] & 0b10000000:
            packed = pad + packed
    else:
        pad = b'\xff'
        packed = _struct_int64.pack(val).lstrip(pad) or pad
        if not packed[0] & 0b10000000:
            packed = pad + packed

    if length is None:
        return packed
    if len(packed) > length:
        raise ValueError("Encoded length (%d) greater than specified length "
                         "(%d)" % (len(packed), length))
    return packed.rjust(length, pad)


def encodeFloat(val, length=None):
    """ Encode a floating point value.

        @param val: The floating point value to encode.
        @keyword length: An explicit length for the encoded data. Must be
            `None`, 0, 4, or 8; otherwise, a `ValueError` will be raised.
        @return: The binary representation of val as a float, left-padded with
            ``0x00`` if `length` is not `None`.
        @raise ValueError: raised if val not length 0, 4, or 8
    """
    if length is None:
        if val is None or val == 0.0:
            return b''
        else:
            length = DEFAULT_FLOAT_SIZE

    if length == 0:
        return b''
    if length == 4:
        return _struct_float32.pack(val)
    elif length == 8:
        return _struct_float64.pack(val)
    else:
        raise ValueError("Cannot encode float of length %d; only 0, 4, or 8" %
                         length)


def encodeBinary(val, length=None):
    """ Encode binary data.

        @param val: A string or bytearray containing the data to encode.
        @keyword length: An explicit length for the encoded data. A
            `ValueError` will be raised if `length` is shorter than the
            actual length of the binary data.
        @return: The binary representation of value as binary data, left-padded
            with ``0x00`` if `length` is not `None`.
        @raise ValueError: raised if val is longer than length.
    """
    if isinstance(val, str):
        val = val.encode('utf_8')
    elif val is None:
        val = b''

    if length is None:
        return val
    elif len(val) <= length:
        return val.ljust(length, b'\x00')
    else:
        raise ValueError("Length of data (%d) exceeds specified length (%d)" %
                         (len(val), length))


def encodeString(val, length=None):
    """ Encode an ASCII string.

        @param val: The string (or bytearray) to encode.
        @keyword length: An explicit length for the encoded data. Longer
            strings will be truncated.
        @keyword length: An explicit length for the encoded data. The result
            will be truncated if the length is less than that of the original.
        @return: The binary representation of val as a string, truncated or
            left-padded with ``0x00`` if `length` is not `None`.
    """
    if isinstance(val, str):
        val = val.encode('ascii', 'replace')

    if length is not None:
        val = val[:length]

    return encodeBinary(val.translate(STRING_CHARACTERS), length)


def encodeUnicode(val, length=None):
    """ Encode a Unicode string.

        @param val: The Unicode string to encode.
        @keyword length: An explicit length for the encoded data. The result
            will be truncated if the length is less than that of the original.
        @return: The binary representation of val as a string, truncated or
            left-padded with ``0x00`` if `length` is not `None`.
    """
    val = val.encode('utf_8')

    if length is not None:
        val = val[:length]

    return encodeBinary(val, length)


def encodeDate(val, length=None):
    """ Encode a `datetime` object as an EBML date (i.e. nanoseconds since
        2001-01-01T00:00:00).

        @param val: The `datetime.datetime` object value to encode.
        @keyword length: An explicit length for the encoded data. Must be
            `None` or 8; otherwise, a `ValueError` will be raised.
        @return: The binary representation of val as an 8-byte dateTime.
        @raise ValueError: raised if the length of the input is not 8 bytes.
    """
    if length is None:
        length = 8
    elif length != 8:
        raise ValueError("Dates must be of length 8")

    if val is None:
        val = datetime.datetime.utcnow()

    delta = val - datetime.datetime(2001, 1, 1, tzinfo=None)
    nanoseconds = (delta.microseconds +
                   ((delta.seconds + (delta.days * 86400)) * 1000000)) * 1000
    return encodeInt(nanoseconds, length)
