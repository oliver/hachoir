from hachoir_core.field import (FieldSet, ParserError,
    Bit, UInt8, UInt16, UInt32, TimestampUnix32,
    Bytes, String, Enum,
    PaddingBytes, PaddingBits, NullBytes, NullBits)
from hachoir_core.text_handler import hexadecimal, humanFilesize

class SectionHeader(FieldSet):
    static_size = 40 * 8
    def createFields(self):
        yield String(self, "name", 8, charset="ASCII", strip="\0 ")
        yield UInt32(self, "mem_size", "Size in memory", text_handler=humanFilesize)
        yield UInt32(self, "rva", "RVA (location) in memory", text_handler=hexadecimal)
        yield UInt32(self, "phys_size", "Physical size (on disk)", text_handler=humanFilesize)
        yield UInt32(self, "phys_off", "Physical location (on disk)", text_handler=humanFilesize)
        yield PaddingBytes(self, "reserved", 12)
        if False:
            yield UInt32(self, "flags", text_handler=hexadecimal)
        else:
            # 0x0000000#
            yield NullBits(self, "reserved[]", 4)
            # 0x000000#0
            yield NullBits(self, "reserved[]", 1)
            yield Bit(self, "has_code", "Contains code")
            yield Bit(self, "has_init_data", "Contains initialized data")
            yield Bit(self, "has_uinit_data", "Contains uninitialized data")
            # 0x00000#00
            yield NullBits(self, "reserved[]", 1)
            yield Bit(self, "has_comment", "Contains comments?")
            yield NullBits(self, "reserved[]", 1)
            yield Bit(self, "remove", "Contents will not become part of image")
            # 0x0000#000
            yield Bit(self, "has_comdata", "Contains comdat?")
            yield NullBits(self, "reserved[]", 1)
            yield Bit(self, "no_defer_spec_exc", "Reset speculative exceptions handling bits in the TLB entries")
            yield Bit(self, "gp_rel", "Content can be accessed relative to GP")
            # 0x000#0000
            yield NullBits(self, "reserved[]", 4)
            # 0x00#00000
            yield NullBits(self, "reserved[]", 4)
            # 0x0#000000
            yield Bit(self, "ext_reloc", "Contains extended relocations?")
            yield Bit(self, "discarded", "Can be discarded?")
            yield Bit(self, "is_not_cached", "Is not cachable?")
            yield Bit(self, "is_not_paged", "Is not pageable?")
            # 0x#0000000
            yield Bit(self, "is_shareable", "Is shareable?")
            yield Bit(self, "is_executable", "Is executable?")
            yield Bit(self, "is_readable", "Is readable?")
            yield Bit(self, "is_writable", "Is writable?")

    def rva2file(self, rva):
        return self["phys_off"].value + (rva - self["rva"].value)

    def createDescription(self):
        info = [
            "rva=%s" % self["rva"].display,
            "size=%s" % self["mem_size"].display]
        if self["is_executable"].value:
            info.append("exec")
        if self["is_readable"].value:
            info.append("read")
        if self["is_writable"].value:
            info.append("write")
        return 'Section "%s": %s' % (self["name"].value, ", ".join(info))

class DataDirectory(FieldSet):
    def createFields(self):
        yield UInt32(self, "rva", "Virtual address", text_handler=hexadecimal)
        yield UInt32(self, "size", text_handler=humanFilesize)

    def createDescription(self):
        if self["size"].value:
            return "Directory at %s (%s)" % (
                self["rva"].display, self["size"].display)
        else:
            return "(empty directory)"

class PE_Header(FieldSet):
    static_size = 24*8
    cpu_name = {
        0x0184: u"Alpha AXP",
        0x01c0: u"ARM",
        0x014C: u"Intel 80386",
        0x014D: u"Intel 80486",
        0x014E: u"Intel Pentium",
        0x0200: u"Intel IA64",
        0x0268: u"Motorolla 68000",
        0x0266: u"MIPS",
        0x0284: u"Alpha AXP 64 bits",
        0x0366: u"MIPS with FPU",
        0x0466: u"MIPS16 with FPU",
        0x01f0: u"PowerPC little endian",
        0x0162: u"R3000",
        0x0166: u"MIPS little endian (R4000)",
        0x0168: u"R10000",
        0x01a2: u"Hitachi SH3",
        0x01a6: u"Hitachi SH4",
        0x0160: u"R3000 (MIPS), big endian",
        0x0162: u"R3000 (MIPS), little endian",
        0x0166: u"R4000 (MIPS), little endian",
        0x0168: u"R10000 (MIPS), little endian",
        0x0184: u"DEC Alpha AXP",
        0x01F0: u"IBM Power PC, little endian",
    }

    def createFields(self):
        yield Bytes(self, "header", 4, r"PE header signature (PE\0\0)")
        if self["header"].value != "PE\0\0":
            raise ParserError("Invalid PE header signature")
        yield Enum(UInt16(self, "cpu", "CPU type"), self.cpu_name)
        yield UInt16(self, "nb_section", "Number of sections")
        yield TimestampUnix32(self, "creation_date", "Creation date")
        yield UInt32(self, "ptr_to_sym", "Pointer to symbol table")
        yield UInt32(self, "nb_symbols", "Number of symbols")
        yield UInt16(self, "opt_hdr_size", "Optional header size")

        yield Bit(self, "reloc_stripped", "If true, don't contain base relocations.")
        yield Bit(self, "exec_image", "Exectuable image?")
        yield Bit(self, "line_nb_stripped", "COFF line numbers stripped?")
        yield Bit(self, "local_sym_stripped", "COFF symbol table entries stripped?")
        yield Bit(self, "aggr_ws", "Aggressively trim working set")
        yield Bit(self, "large_addr", "Application can handle addresses greater than 2 GB")
        yield NullBits(self, "reserved", 1)
        yield Bit(self, "reverse_lo", "Little endian: LSB precedes MSB in memory")
        yield Bit(self, "32bit", "Machine based on 32-bit-word architecture")
        yield Bit(self, "is_stripped", "Debugging information removed?")
        yield Bit(self, "swap", "If image is on removable media, copy and run from swap file")
        yield PaddingBits(self, "reserved2", 1)
        yield Bit(self, "is_system", "It's a system file")
        yield Bit(self, "is_dll", "It's a dynamic-link library (DLL)")
        yield Bit(self, "up", "File should be run only on a UP machine")
        yield Bit(self, "reverse_hi", "Big endian: MSB precedes LSB in memory")

class PE_OptHeader(FieldSet):
    SUBSYSTEM_NAME = {
        1: u"Native",
        2: u"Windows/GUI",
        3: u"Windows non-GUI",
        5: u"OS/2",
        7: u"POSIX",
    }
    DIRECTORY_NAME = {
        0: "export",
        1: "import",
        2: "resource",
        3: "exception_table",
        4: "certificate_table",
        11: "bound_import",
    }
    def createFields(self):
        yield UInt16(self, "signature", "PE optional header signature (0x010b)")
        # TODO: Support PE32+ (signature=0x020b)
        if self["signature"].value != 0x010b:
            raise ParserError("Invalid PE optional header signature")
        yield UInt8(self, "maj_lnk_ver", "Major linker version")
        yield UInt8(self, "min_lnk_ver", "Minor linker version")
        yield UInt32(self, "size_code", "Size of code", text_handler=humanFilesize)
        yield UInt32(self, "size_init_data", "Size of initialized data", text_handler=humanFilesize)
        yield UInt32(self, "size_uninit_data", "Size of uninitialized data", text_handler=humanFilesize)
        yield UInt32(self, "entry_point", "Address (RVA) of the code entry point", text_handler=hexadecimal)
        yield UInt32(self, "base_code", "Base (RVA) of code", text_handler=hexadecimal)
        yield UInt32(self, "base_data", "Base (RVA) of data", text_handler=hexadecimal)
        yield UInt32(self, "image_base", "Image base (RVA)", text_handler=hexadecimal)
        yield UInt32(self, "sect_align", "Section alignment", text_handler=humanFilesize)
        yield UInt32(self, "file_align", "File alignment", text_handler=humanFilesize)
        yield UInt16(self, "maj_os_ver", "Major OS version")
        yield UInt16(self, "min_os_ver", "Minor OS version")
        yield UInt16(self, "maj_img_ver", "Major image version")
        yield UInt16(self, "min_img_ver", "Minor image version")
        yield UInt16(self, "maj_subsys_ver", "Major subsystem version")
        yield UInt16(self, "min_subsys_ver", "Minor subsystem version")
        yield NullBytes(self, "reserved", 4)
        yield UInt32(self, "size_img", "Size of image", text_handler=humanFilesize)
        yield UInt32(self, "size_hdr", "Size of headers", text_handler=humanFilesize)
        yield UInt32(self, "checksum", text_handler=hexadecimal)
        yield Enum(UInt16(self, "subsystem"), self.SUBSYSTEM_NAME)
        yield UInt16(self, "dll_flags")
        yield UInt32(self, "size_stack_reserve", text_handler=humanFilesize)
        yield UInt32(self, "size_stack_commit", text_handler=humanFilesize)
        yield UInt32(self, "size_heap_reserve", text_handler=humanFilesize)
        yield UInt32(self, "size_heap_commit", text_handler=humanFilesize)
        yield UInt32(self, "loader_flags")
        yield UInt32(self, "nb_directory", "Number of RVA and sizes")
        for index in xrange(self["nb_directory"].value):
            try:
                name = self.DIRECTORY_NAME[index]
            except KeyError:
                name = "data_dir[%u]" % index
            yield DataDirectory(self, name)

