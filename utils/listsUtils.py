import re

ORDER_LIST_PATTERN = re.compile(r"(\s*[(]?)(\d+|[a-y]|[A-Y])([.)]\s+)(.*)")
UNORDER_LIST_PATTERN = re.compile(r"(\s*(?:[-+|*]+|[(]?#[).]))(\s+)\S+")
EMPTY_LIST_PATTERN = re.compile(r"(\s*)([-+*]|[(]?(?:\d+|[a-y]|[A-Y]|#|[MDCLXVImdclxvi]+)[.)])(\s+)$")
NONLIST_PATTERN = re.compile(r"(\s*[>|%]+)(\s+)\S?")
ROMAN_PATTERN = re.compile(r"(\s*[(]?)(M{0,4}CM|CD|D?C{0,3}XC|XL|L?X{0,3}IX|IV|V?I{0,3})([.)]\s+)(.*)",
                           re.IGNORECASE)
#Define digit mapping
ROMAN_MAP = (('M', 1000),
             ('CM', 900),
             ('D', 500),
             ('CD', 400),
             ('C', 100),
             ('XC', 90),
             ('L', 50),
             ('XL', 40),
             ('X', 10),
             ('IX', 9),
             ('V', 5),
             ('IV', 4),
             ('I', 1))

#Define exceptions
class RomanError(Exception): pass
class NotIntegerError(RomanError): pass
class InvalidRomanNumeralError(RomanError): pass


def to_roman(n):
    """convert integer to Roman numeral"""
    if not (0 < n < 5000):
        raise Exception("number out of range (must be 1..4999)")
    result = ""
    for numeral, integer in ROMAN_MAP:
        while n >= integer:
            result += numeral
            n -= integer
    return result

def from_roman(s):
    """convert Roman numeral to integer"""
    result = 0
    index = 0
    for numeral, integer in ROMAN_MAP:
        while s[index:index + len(numeral)] == numeral:
            result += integer
            index += len(numeral)
    return result