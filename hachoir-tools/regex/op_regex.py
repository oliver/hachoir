from regex import RegexAnd, RegexOr, RegexString
from parser import parse
import re

def groupStringsLen(patterns, prefix_len):
    """
    Group string with the prefix of 'prefix_len' characters.
    patterns is a list of sorted strings.
    Returns (nb_grouped, groups, tail)

    >>> groupStrings( ["abc", "abd", "xyz"])
    ({'ab': ['c', 'd']}, ['xyz'])
    >>> groupStrings( ["abcd0", "abcd01", "abcd2"])
    ({'abcd': ['0', '01', '2']}, [])
    >>> groupStrings( ["abc", "abc"])
    ({'abc': ['', '']}, [])

    >>> groupStrings( ["ab", "abc", "deF", "def"])
    ({'de': ['F', 'f'], 'ab': ['', 'c']}, [])
    """

    groups = {}
    tail = []
    nb_grouped = 0
    start = 0
    while start < len(patterns):
        prefix = patterns[start][:prefix_len]
        index = start+1
        count = 1
        while index < len(patterns) and patterns[index].startswith(prefix):
            count += 1
            index += 1
        if 1 < count:
            groups[prefix] = [ patterns[index][prefix_len:] for index in xrange(start,start+count) ]
            nb_grouped += count
            start += count
        else:
            tail.append(patterns[start])
            start += 1
        #tail.extend( patterns[start+count:] )
    return nb_grouped, groups, tail

def createRegex(patterns):
    r"""
    Create fast regex to match all strings of 'patterns' list.

    >>> print createRegex(["func(b)"])
    func\(b\)
    >>> print createRegex(["a", "b"])
    [ab]
    >>> print createRegex(["aa", "bb"])
    (?:aa|bb)
    >>> print createRegex(["name0", "name1"])
    name[01]
    >>> print createRegex(["name1201", "name1001", "name1202"])
    name1(?:20[12]|001)
    >>> print createRegex([".exe", ".ico"])
    \.(?:exe|ico)
    """
    # Just one string?
    if len(patterns) == 1:
        return re.escape(patterns[0])

    # All pattern are 1 character?
    index = 0
    while index < len(patterns):
        if len(patterns[index]) != 1:
            break
        index += 1
    if index == len(patterns):
        regex = "".join(patterns)
        return "[%s]" % regex

    groups, tail = groupStrings(patterns)
    regex = []
    if groups:
        for prefix, patterns in groups.iteritems():
            regex.append(re.escape(prefix) + createRegex(patterns))
    else:
        tail = patterns
    for pattern in tail:
        regex.append(re.escape(pattern))
    if 2 <= len(regex):
        return "(?:%s)" % "|".join(regex)
    else:
        return regex[0]

def groupStrings(patterns):
    """
    Group string with the smaller prefix (with minimum length of 1 character).

    >>> groupStrings( ["abc", "xyz", "abd"])
    ({'ab': ['c', 'd']}, ['xyz'])
    >>> groupStrings( ["abcd0", "abcd01", "abcd2"])
    ({'abcd': ['0', '01', '2']}, [])
    >>> groupStrings( ["abc", "abc"])
    ({'abc': ['', '']}, [])

    >>> groupStrings( ["ab", "abc", "deF", "def"])
    ({'de': ['F', 'f'], 'ab': ['', 'c']}, [])
    """
    patterns = sorted(patterns)
    nb_grouped, groups, tail = groupStringsLen(patterns, 1)
    min_len = min( len(pattern) for pattern in patterns )
    prefix_len = 2
    while prefix_len <= min_len:
        new_nb_grouped, new_groups, new_tail = groupStringsLen(patterns, prefix_len)
        if new_nb_grouped < nb_grouped:
            break
        groups, tail = new_groups, new_tail
        prefix_len += 1
    return groups, tail

def optimizeOr(regex):
    text = []
    other = []
    for item in regex.content:
        if item.__class__ == RegexString:
            text.append(item)
        else:
            other.append(item)
    if len(text) < 2:
        return None

#    ({'ab': ['c', 'd']}, ['xyz'])
    groups, tail = groupStrings(str(item) for item in text)
    if not groups:
        return
    groups_regex = []
    for common, group in groups.iteritems():
        regex = RegexString(common)
        if group[0]:
            regex_or = RegexOr( RegexString(item) for item in group )
            regex = RegexAnd( (regex, regex_or) )
        groups_regex.append(regex)
    regex = RegexOr.join(groups_regex)
    if tail:
        regex = regex |  RegexOr.join( RegexString(item) for item in tail )
    if other:
        regex = regex | RegexOr(other)
    return regex


def optimize(regex):
    """
    >>> optimize(parse('(color red|color blue)'))
    <RegexAnd 'color (blue|red)'>
    >>> optimize(parse('(color blue|color red|no color)'))
    <RegexOr '(color (blue|red)|no color)'>
    """
    cls = regex.__class__
    if issubclass(cls, RegexAnd):
        for item in regex.content:
            optimize(item)
    if cls == RegexOr:
        new = optimizeOr(regex)
        if new:
            regex = new
    return regex

if __name__ == "__main__":
    import doctest
    doctest.testmod()

