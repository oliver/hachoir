from hachoir_core.field import (FieldSet,
    UInt16, UInt32, Enum, String, Bytes, Bits)
from hachoir_parser.video.fourcc import video_fourcc_name
from hachoir_core.bits import str2hex
from hachoir_core.text_handler import textHandler, hexadecimal
from hachoir_parser.network.common import OrganizationallyUniqueIdentifier, MAC48_Address
from hachoir_core.tools import timestampUUID60

def formatTimestamp(field):
    return timestampUUID60(field.value)

class GUID(FieldSet):
    """
    Windows 128 bits Globally Unique Identifier (GUID)

    See RFC 4122
    """
    static_size = 128
    NULL = "00000000-0000-0000-0000-000000000000"
    FIELD_NAMES = {
        3: ("sha1_high", "sha1_low"),
        4: ("random_high", "random_low"),
        5: ("md5_high", "md5_low"),
    }
    VERSION_NAME = {
        1: "Timestamp & MAC-48",
        2: "DCE Security version",
        3: "Name SHA-1 hash",
        4: "Randomly generated",
        5: "Name MD5 hash",
    }
    VARIANT_NAME = {
        0: "NCS",
        2: "Leach-Salz",
       # 5: Microsoft Corporation?
        6: "Microsoft Corporation",
        7: "Reserved Future",
    }
    def __init__(self, *args):
        FieldSet.__init__(self, *args)
        self.version = self.stream.readBits(self.absolute_address + 32 + 16 + 12, 4, self.endian)

    def createFields(self):
        if self.version == 1:
            yield textHandler(Bits(self, "time", 60), formatTimestamp)
            yield Enum(Bits(self, "version", 4), self.VERSION_NAME)
            yield Enum(Bits(self, "variant", 3), self.VARIANT_NAME)
            yield textHandler(Bits(self, "clock", 13), hexadecimal)
#            yield textHandler(Bits(self, "clock", 16), hexadecimal)
            if self.version == 1:
                yield MAC48_Address(self, "mac", "IEEE 802 MAC address")
            else:
                yield Bytes(self, "node", 6)
        else:
            namea, nameb = self.FIELD_NAMES.get(
                self.version, ("data_a", "data_b"))
            yield textHandler(Bits(self, namea, 60), hexadecimal)
            yield Enum(Bits(self, "version", 4), self.VERSION_NAME)
            yield Enum(Bits(self, "variant", 3), self.VARIANT_NAME)
            yield textHandler(Bits(self, nameb, 61), hexadecimal)

    def createValue(self):
        addr = self.absolute_address
        a = self.stream.readBits (addr,      32, self.endian)
        b = self.stream.readBits (addr + 32, 16, self.endian)
        c = self.stream.readBits (addr + 48, 16, self.endian)
        d = self.stream.readBytes(addr + 64, 2)
        e = self.stream.readBytes(addr + 80, 6)
        return "%08X-%04X-%04X-%s-%s" % (a, b, c, str2hex(d), str2hex(e))

    def createDisplay(self):
        value = self.value
        if value == self.NULL:
            name = "Null GUID: "
        else:
            name = "GUID v%u (%s): " % (self.version, self["version"].display)
        return name + value

    def createRawDisplay(self):
        value = self.stream.readBytes(self.absolute_address, 16)
        return str2hex(value, format=r"\x%02x")

class BitmapInfoHeader(FieldSet):
    """ Win32 BITMAPINFOHEADER structure from GDI """
    static_size = 40*8

    COMPRESSION_NAME = {
        0: u"Uncompressed (RGB)",
        1: u"RLE (8 bits)",
        2: u"RLE (4 bits)",
        3: u"Bitfields",
        4: u"JPEG",
        5: u"PNG"
    }

    def __init__(self, parent, name, use_fourcc=False):
        FieldSet.__init__(self, parent, name)
        self._use_fourcc = use_fourcc

    def createFields(self):
        yield UInt32(self, "hdr_size", "Header size (in bytes) (=40)")
        yield UInt32(self, "width", "Width")
        yield UInt32(self, "height", "Height")
        yield UInt16(self, "nb_planes", "Color planes")
        yield UInt16(self, "bpp", "Bits/pixel")
        if self._use_fourcc:
            yield Enum(String(self, "codec", 4, charset="ASCII"), video_fourcc_name)
        else:
            yield Enum(UInt32(self, "codec", "Compression"), self.COMPRESSION_NAME)
        yield UInt32(self, "size", "Image size (in bytes)")
        yield UInt32(self, "xres", "X pixels per meter")
        yield UInt32(self, "yres", "Y pixels per meter")
        yield UInt32(self, "color_used", "Number of used colors")
        yield UInt32(self, "color_important", "Number of important colors")

    def createDescription(self):
        return "Bitmap info header: %ux%u pixels, %u bits/pixel" % \
            (self["width"].value, self["height"].value, self["bpp"].value)

