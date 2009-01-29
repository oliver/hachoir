"""
Parallel Realities Starfighter .pak file parser

See http://www.parallelrealities.co.uk/projects/starfighter.php

Author: Oliver Gerlich
Creation date: 2008-01-29
"""

from hachoir_parser import Parser
from hachoir_core.field import (ParserError,
    UInt8, UInt16, UInt32, String, RawBytes)
from hachoir_core.endian import LITTLE_ENDIAN, BIG_ENDIAN

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

        # Read rest of the file (if any)
        if self.current_size < self._size:
            yield self.seekBit(self._size, "end")
