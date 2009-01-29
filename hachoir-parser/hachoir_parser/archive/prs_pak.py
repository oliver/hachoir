"""
Parallel Realities Starfighter .pak file parser

See http://www.parallelrealities.co.uk/projects/starfighter.php

Author: Oliver Gerlich
Creation date: 2008-01-29
"""

from hachoir_parser import Parser
from hachoir_core.field import (ParserError,
    UInt8, UInt16, UInt32, String, RawBytes, FieldSet)
from hachoir_core.endian import LITTLE_ENDIAN, BIG_ENDIAN

class FileEntry(FieldSet):
    def createFields(self):
        yield String(self, "filename", 56)
        yield UInt32(self, "size")
        yield RawBytes(self, "data", self["size"].value)


class PRSPakFile(Parser):
    PARSER_TAGS = {
        "id": "prs_pak",
        "category": "archive",
        "file_ext": ("pak",),
        "mime": (u"application/octet-stream",),
        "min_size": 4*8,
        "description": "Parallel Realities Starfighter .pak archive",
    }

    endian = LITTLE_ENDIAN

    def validate(self):
        return (self.stream.readBytes(0, 4) == 'PACK')

    def createFields(self):
        yield String(self, "magic", 4)

        # all remaining data must be file entries:
        while self.current_size < self._size:
            yield FileEntry(self, "file[]")
