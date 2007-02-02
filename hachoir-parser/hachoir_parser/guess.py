"""
Parser list managment:
- createParser() find the best parser for a file.
"""

import os
from hachoir_core.error import warning, info, HACHOIR_ERRORS
from hachoir_parser import ValidateError, HachoirParserList
from hachoir_core.stream import FileInputStream
from hachoir_core.i18n import _


class QueryParser(object):
    fallback = None
    other = None

    def __init__(self, tags):
        self.db = HachoirParserList()
        self.parsers = set(self.db)
        parsers = []
        for tag in tags:
            if not self.parsers:
                break
            parsers += self._getByTag(tag)
            if self.fallback is None:
                self.fallback = len(parsers) == 1
        if self.parsers:
            other = len(parsers)
            parsers += list(self.parsers)
            self.other = parsers[other]
        self.parsers = parsers

    def __iter__(self):
        return iter(self.parsers)

    def translate(self, name, value):
        if name == "filename":
            filename = os.path.basename(value).split(".")
            if len(filename) <= 1:
                value = ""
            else:
                value = filename[-1].lower()
            name = "file_ext"
        return name, value

    def _getByTag(self, tag):
        if tag is None:
            self.parsers.clear()
            return []
        elif callable(tag):
            parsers = [ parser for parser in self.parsers if tag(parser) ]
            for parser in parsers:
                self.parsers.remove(parser)
        else:
            tag = self.translate(*tag)
            parsers = []
            if tag is not None:
                byname = self.db.bytag.get(tag[0],{})
                if tag[1] is None:
                    values = byname.itervalues()
                else:
                    values = byname.get(tag[1],()),
                for value in values:
                    for parser in value:
                        if parser in self.parsers:
                            parsers.append(parser)
                            self.parsers.remove(parser)
        return parsers

    def parse(self, stream, fallback=True):
        fb = None
        warn = warning
        for parser in self.parsers:
            if stream.size < parser.getTags()['min_size']:
                continue
            try:
                return parser(stream, validate=True)
            except ValidateError, err:
                res = unicode(err)
                if fallback and self.fallback:
                    fb = parser
            except HACHOIR_ERRORS, err:
                res = unicode(err)
            if warn:
                if parser == self.other:
                    warn = info
                warn(_("Skip parser '%s': %s") % (parser.__name__, res))
            fallback = False
        if fb:
            warning(_("Force use of parser '%s'") % fb.__name__)
            return fb(stream)


def guessParser(stream):
    return QueryParser(stream.tags).parse(stream)


def createParser(filename, real_filename=None):
    """
    Create a parser from a file or returns None on error.

    Options:
    - filename (unicode): Input file name ;
    - real_filename (str|unicode): Real file name.
    """
    return guessParser(FileInputStream(filename, real_filename))
