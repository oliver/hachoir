import re

def escapeRegex(text):
    # Escape "^.+*?{}[]|()\\$": add "\"
    return re.sub(r"([][^.+*?{}|()\\$])", r"\\\1", text)

class Regex:
    def minLength(self):
        """
        Maximum length in characters of the regex.
        Returns None if there is no limit.
        """
        raise NotImplementedError()

    def maxLength(self):
        """
        Maximum length in characters of the regex.
        Returns None if there is no limit.
        """
        return self.minLength()

    def __str__(self):
        raise NotImplementedError()

    def __repr__(self):
        return "<%s '%s'>" % (
            self.__class__.__name__, self)

    def _and(self, regex):
        """
        Create new optimized version of a+b.
        Returns None if there is no interesting optimization.
        """
        if self.__class__ == RegexEmpty:
            return regex
        return None

    def __add__(self, regex):
        """
        >>> RegexEmpty() + RegexString('a')
        <RegexString 'a'>
        """
        new_regex = self._and(regex)
        if new_regex:
            return new_regex
        else:
            return RegexAnd( (self, regex) )

    def _or(self, regex):
        """
        Create new optimized version of a|b.
        Returns None if there is no interesting optimization.
        """
        return None

    def __or__(self, regex):
        new_regex = self._or(regex)
        if new_regex:
            return new_regex
        else:
            return RegexOr( (self, regex) )

    def __eq__(self, regex):
        # TODO: Write better code...
        return str(self) == str(regex)

class RegexEmpty(Regex):
    def minLength(self):
        return 0

    def __str__(self):
        return ''

    def __repr__(self):
        return "<RegexEmpty>"

    def _and(self, regex):
        return regex

class RegexString(Regex):
    def __init__(self, text=""):
        assert isinstance(text, str)
        self._text = text

    def minLength(self):
        return len(self._text)

    def _and(self, regex):
        """
        >>> RegexString('a') + RegexString('b')
        <RegexString 'ab'>
        """
        if regex.__class__ == RegexString:
            return RegexString(self._text + regex._text)
        return None

    def __str__(self):
        return escapeRegex(self._text)

    def _or(self, regex):
        """
        Remove duplicate:
        >>> RegexString("color") | RegexString("color")
        <RegexString 'color'>

        Group prefix:

        >>> RegexString("moot") | RegexString("boot")
        <RegexAnd '[mb]oot'>
        >>> RegexString("color red") | RegexString("color blue")
        <RegexAnd 'color (red|blue)'>
        >>> RegexString("color red") | RegexString("color")
        <RegexAnd 'color( red|)'>

        Group suffix:

        >>> RegexString("good thing") | RegexString("blue thing")
        <RegexAnd '(good|blue) thing'>
        """
        # (a|[bc]) => [abc]
        if regex.__class__ == RegexRange and len(self._text) == 1:
            return RegexRange(self._text) | regex

        if regex.__class__ != RegexString:
            return None
        texta = self._text
        textb = regex._text
        if texta == textb:
            return self

        # Find common prefix
        common = None
        for length in xrange(1, min(len(texta),len(textb))+1):
            if textb.startswith(texta[:length]):
                common = length
            else:
                break
        if common:
            return RegexString(texta[:common]) + (RegexString(texta[common:]) | RegexString(textb[common:]))

        # Find common suffix
        common = None
        for length in xrange(1, min(len(texta),len(textb))+1):
            if textb.endswith(texta[-length:]):
                common = length
            else:
                break
        if common:
            return ((RegexString(texta[:-common]) | RegexString(textb[:-common]))) + RegexString(texta[-common:])

        # (a|b) => [ab]
        if len(texta) == len(textb) == 1:
            return RegexRange(texta+textb)
        return None

class RegexRange(Regex):
    def __init__(self, char_range, exclude=False):
        self.range = char_range
        self.exclude = exclude

    def minLength(self):
        return 1

    def _or(self, regex):
        """
        >>> RegexRange("a") | RegexRange("b")
        <RegexRange '[ab]'>
        >>> RegexRange("^ab") | RegexRange("^ac")
        <RegexRange '[^abc]'>
        """
        new_range = None
        if not self.exclude and regex.__class__ == RegexString and len(regex._text) == 1:
            new_range = regex._text
        elif regex.__class__ == RegexRange and self.exclude == regex.exclude:
            new_range = regex.range
        if not new_range:
            return None
        crange = self.range
        for character in new_range:
            if character not in crange:
                crange += character
        return RegexRange(crange, self.exclude)

    def __str__(self):
        if self.exclude:
            return "[^%s]" % self.range
        else:
            return "[%s]" % self.range

class RegexAndOr(Regex):
    def __contains__(self, regex):
        for item in self.content:
            if item == regex:
                return True
        return False

class RegexAnd(RegexAndOr):
    def __init__(self, items):
        self.content = []
        for item in items:
            if item.__class__ == RegexEmpty:
                continue
            if self.content \
            and self.content[-1].__class__ == item.__class__ == RegexString:
                self.content[-1] = RegexString(self.content[-1]._text + item._text)
            else:
                self.content.append(item)
        assert 2 <= len(self.content)

    def _minmaxLength(self, lengths):
        total = 0
        for length in lengths:
            if length is None:
                return None
            total += length
        return total

    def minLength(self):
        """
        >>> regex=((RegexString('a') | RegexString('bcd')) + RegexString('z'))
        >>> regex.minLength()
        2
        """
        return self._minmaxLength( regex.minLength() for regex in self.content )

    def maxLength(self):
        """
        >>> regex=RegexOr((RegexString('a'), RegexString('bcd')))
        >>> RegexAnd((regex, RegexString('z'))).maxLength()
        4
        """
        return self._minmaxLength( regex.maxLength() for regex in self.content )

    def _and(self, regex):
        """
        >>> RegexRange('ab') + RegexRange('01')
        <RegexAnd '[ab][01]'>
        >>> RegexRange('01') + RegexString('a') + RegexString('b')
        <RegexAnd '[01]ab'>
        """

        if regex.__class__ == RegexAnd:
            total = self
            for item in regex.content:
                total = total + item
            return total
        if regex in self:
            return self
        new_item = self.content[-1]._and(regex)
        if new_item:
            self.content[-1] = new_item
            return self
        return RegexAnd( self.content + [regex] )

    def __str__(self):
        return ''.join( str(item) for item in self.content )

class RegexOr(RegexAndOr):
    def __init__(self, items):
        self.content = []
        for item in items:
            if item in self:
                continue
            self.content.append(item)
        assert 2 <= len(self.content)

    def _or(self, regex):
        """
        >>> (RegexString("abc") | RegexString("123")) | (RegexString("plop") | RegexString("456"))
        <RegexOr '(abc|123|plop|456)'>
        >>> RegexOr((RegexString("ab"), RegexRange("c"))) | RegexOr((RegexString("de"), RegexRange("f")))
        <RegexOr '(ab|[cf]|de)'>
        """
        if regex.__class__ == RegexOr:
            total = self
            for item in regex.content:
                total = total | item
            return total
        if regex in self:
            return self
        for index, item in enumerate(self.content):
            new_item = item._or(regex)
            if new_item:
                self.content[index] = new_item
                return self
        return RegexOr( self.content + [regex] )

    def __str__(self):
        content = '|'.join( str(item) for item in self.content )
        return "(%s)" % content

    def _minmaxLength(self, lengths, func):
        value = None
        for length in lengths:
            if length is None:
                return None
            if value is None:
                value = length
            else:
                value = func(value, length)
        return value

    def minLength(self):
        lengths = ( regex.minLength() for regex in self.content )
        return self._minmaxLength(lengths, min)

    def maxLength(self):
        lengths = ( regex.maxLength() for regex in self.content )
        return self._minmaxLength(lengths, max)

if __name__ == "__main__":
    import doctest
    doctest.testmod()

