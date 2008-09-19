from hachoir_core.field import (FieldSet,
    Bit, Bits,
    UInt8, Int16, UInt16, UInt32, Int32,
    NullBytes, RawBytes, PascalString16,
    DateTimeMSDOS32)

class WordDocument(FieldSet):
    def createFields(self):
        yield UInt16(self, "magic")
        yield UInt16(self, "nFib")
        yield UInt16(self, "nProduct")
        yield UInt16(self, "lid")
        yield Int16(self, "pnNext")

        yield Bit(self, "fDot")
        yield Bit(self, "fGlsy")
        yield Bit(self, "fComplex")
        yield Bit(self, "fHasPic")
        yield Bits(self, "cQuickSaves", 4)
        yield Bit(self, "fEncrypted")
        yield Bit(self, "fWhichTblStm")
        yield Bit(self, "fReadOnlyRecommanded")
        yield Bit(self, "fWriteReservation")
        yield Bit(self, "fExtChar")
        yield Bit(self, "fLoadOverride")
        yield Bit(self, "fFarEeast")
        yield Bit(self, "fCrypto")

        yield UInt16(self, "nFibBack")
        yield UInt32(self, "IKey")
        yield UInt8(self, "envr")

        yield Bit(self, "fMac")
        yield Bit(self, "fEmptySpecial")
        yield Bit(self, "fLoadOverridePage")
        yield Bit(self, "fFutureSavedUndo")
        yield Bit(self, "fWord97Save")
        yield Bits(self, "fSpare0", 3)

        yield UInt16(self, "chs")
        yield UInt16(self, "chsTables")
        yield Int32(self, "fcMin")
        yield Int32(self, "fcMac")

        yield PascalString16(self, "file_creator", strip="\0")
        yield NullBytes(self, "reserved", 12)
        yield Int16(self, "lidFE")
        yield UInt16(self, "clw")
        yield Int32(self, "rglw")
        yield DateTimeMSDOS32(self, "lProductCreated")
        yield DateTimeMSDOS32(self, "lProductRevised")

        tail = (self.size - self.current_size) // 8
        if tail:
            yield RawBytes(self, "tail", tail)

