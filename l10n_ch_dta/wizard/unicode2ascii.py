# -*- coding: utf-8 -*-

"""Convert many unicode characters to ascii characters that are like them.

I want to collate names, with the property that a last name starting with
O-umlaut will be in with the last name's starting with O.    Horrors!

So I want that many Latin-1 characters have their umlaute's, etc., stripped.
Some of it can be done automatically but some needs to be done by hand, that
I can tell.
"""
import sys
import unicodedata

__version__ = '1.0.1'
__author__ = 'Jim Hefferon: ftpmaint at tug.ctan.org'
__date__ = '2008-July-15'
__notes__ = """As sources, used effbot's web site, and
    http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/251871
and man uni2ascii
"""

# These characters that are not done automatically by NFKD, and
# have a name starting with "LATIN".    Some of these I found on the interwebs,
# but some I did by eye.    Corrections or additions appreciated.
EXTRA_LATIN_NAMES = {
    # First are ones I got off the interweb
    "\N{LATIN CAPITAL LETTER O WITH STROKE}": "O",
    "\N{LATIN SMALL LETTER A WITH GRAVE}": "a",
    "\N{LATIN SMALL LETTER A WITH ACUTE}": "a",
    "\N{LATIN SMALL LETTER A WITH CIRCUMFLEX}": "a",
    "\N{LATIN SMALL LETTER A WITH TILDE}": "a",
    "\N{LATIN SMALL LETTER A WITH DIAERESIS}": "ae",
    "\N{LATIN SMALL LETTER A WITH RING ABOVE}": "a",
    "\N{LATIN SMALL LETTER C WITH CEDILLA}": "c",
    "\N{LATIN SMALL LETTER E WITH GRAVE}": "e",
    "\N{LATIN SMALL LETTER E WITH ACUTE}": "e",
    "\N{LATIN SMALL LETTER E WITH CIRCUMFLEX}": "e",
    "\N{LATIN SMALL LETTER E WITH DIAERESIS}": "e",
    "\N{LATIN SMALL LETTER I WITH GRAVE}": "i",
    "\N{LATIN SMALL LETTER I WITH ACUTE}": "i",
    "\N{LATIN SMALL LETTER I WITH CIRCUMFLEX}": "i",
    "\N{LATIN SMALL LETTER I WITH DIAERESIS}": "i",
    "\N{LATIN SMALL LETTER N WITH TILDE}": "n",
    "\N{LATIN SMALL LETTER O WITH GRAVE}": "o",
    "\N{LATIN SMALL LETTER O WITH ACUTE}": "o",
    "\N{LATIN SMALL LETTER O WITH CIRCUMFLEX}": "o",
    "\N{LATIN SMALL LETTER O WITH TILDE}": "o",
    "\N{LATIN SMALL LETTER O WITH DIAERESIS}": "oe",
    "\N{LATIN SMALL LETTER U WITH GRAVE}": "u",
    "\N{LATIN SMALL LETTER U WITH ACUTE}": "u",
    "\N{LATIN SMALL LETTER U WITH CIRCUMFLEX}": "u",
    "\N{LATIN SMALL LETTER U WITH DIAERESIS}": "ue",
    "\N{LATIN SMALL LETTER Y WITH ACUTE}": "y",
    "\N{LATIN SMALL LETTER Y WITH DIAERESIS}": "y",
    "\N{LATIN SMALL LETTER A WITH MACRON}": "a",
    "\N{LATIN SMALL LETTER A WITH BREVE}": "a",
    "\N{LATIN SMALL LETTER C WITH ACUTE}": "c",
    "\N{LATIN SMALL LETTER C WITH CIRCUMFLEX}": "c",
    "\N{LATIN SMALL LETTER E WITH MACRON}": "e",
    "\N{LATIN SMALL LETTER E WITH BREVE}": "e",
    "\N{LATIN SMALL LETTER G WITH CIRCUMFLEX}": "g",
    "\N{LATIN SMALL LETTER G WITH BREVE}": "g",
    "\N{LATIN SMALL LETTER G WITH CEDILLA}": "g",
    "\N{LATIN SMALL LETTER H WITH CIRCUMFLEX}": "h",
    "\N{LATIN SMALL LETTER I WITH TILDE}": "i",
    "\N{LATIN SMALL LETTER I WITH MACRON}": "i",
    "\N{LATIN SMALL LETTER I WITH BREVE}": "i",
    "\N{LATIN SMALL LETTER J WITH CIRCUMFLEX}": "j",
    "\N{LATIN SMALL LETTER K WITH CEDILLA}": "k",
    "\N{LATIN SMALL LETTER L WITH ACUTE}": "l",
    "\N{LATIN SMALL LETTER L WITH CEDILLA}": "l",
    "\N{LATIN CAPITAL LETTER L WITH STROKE}": "L",
    "\N{LATIN SMALL LETTER L WITH STROKE}": "l",
    "\N{LATIN SMALL LETTER N WITH ACUTE}": "n",
    "\N{LATIN SMALL LETTER N WITH CEDILLA}": "n",
    "\N{LATIN SMALL LETTER O WITH MACRON}": "o",
    "\N{LATIN SMALL LETTER O WITH BREVE}": "o",
    "\N{LATIN SMALL LETTER R WITH ACUTE}": "r",
    "\N{LATIN SMALL LETTER R WITH CEDILLA}": "r",
    "\N{LATIN SMALL LETTER S WITH ACUTE}": "s",
    "\N{LATIN SMALL LETTER S WITH CIRCUMFLEX}": "s",
    "\N{LATIN SMALL LETTER S WITH CEDILLA}": "s",
    "\N{LATIN SMALL LETTER T WITH CEDILLA}": "t",
    "\N{LATIN SMALL LETTER U WITH TILDE}": "u",
    "\N{LATIN SMALL LETTER U WITH MACRON}": "u",
    "\N{LATIN SMALL LETTER U WITH BREVE}": "u",
    "\N{LATIN SMALL LETTER U WITH RING ABOVE}": "u",
    "\N{LATIN SMALL LETTER W WITH CIRCUMFLEX}": "w",
    "\N{LATIN SMALL LETTER Y WITH CIRCUMFLEX}": "y",
    "\N{LATIN SMALL LETTER Z WITH ACUTE}": "z",
    "\N{LATIN SMALL LETTER W WITH GRAVE}": "w",
    "\N{LATIN SMALL LETTER W WITH ACUTE}": "w",
    "\N{LATIN SMALL LETTER W WITH DIAERESIS}": "w",
    "\N{LATIN SMALL LETTER Y WITH GRAVE}": "y",
    # Below are the ones that failed automated conversion
    '\N{LATIN CAPITAL LETTER AE}': 'AE',
    '\N{LATIN CAPITAL LETTER ETH}': 'D',
    "\N{LATIN CAPITAL LETTER A WITH DIAERESIS}": "Ae",
    "\N{LATIN CAPITAL LETTER O WITH DIAERESIS}": "Oe",
    "\N{LATIN CAPITAL LETTER U WITH DIAERESIS}": "Ue",
    '\N{LATIN CAPITAL LETTER THORN}': 'TH',
    '\N{LATIN SMALL LETTER SHARP S}': 'ss',
    '\N{LATIN SMALL LETTER AE}': 'ae',
    '\N{LATIN SMALL LETTER ETH}': 'd',
    '\N{LATIN SMALL LETTER THORN}': 'th',
    '\N{LATIN CAPITAL LETTER D WITH STROKE}': 'D',
    '\N{LATIN SMALL LETTER D WITH STROKE}': 'd',
    '\N{LATIN CAPITAL LETTER H WITH STROKE}': 'H',
    '\N{LATIN SMALL LETTER H WITH STROKE}': 'h',
    '\N{LATIN SMALL LETTER DOTLESS I}': 'i',
    '\N{LATIN SMALL LETTER KRA}': 'q',
    '\N{LATIN CAPITAL LETTER ENG}': 'N',
    '\N{LATIN SMALL LETTER ENG}': 'n',
    '\N{LATIN CAPITAL LIGATURE OE}': 'OE',
    '\N{LATIN SMALL LIGATURE OE}': 'oe',
    '\N{LATIN CAPITAL LETTER T WITH STROKE}': 'T',
    '\N{LATIN SMALL LETTER T WITH STROKE}': 't',
    '\N{LATIN SMALL LETTER B WITH STROKE}': 'b',
    '\N{LATIN CAPITAL LETTER B WITH HOOK}': 'B',
    '\N{LATIN CAPITAL LETTER B WITH TOPBAR}': 'B',
    '\N{LATIN SMALL LETTER B WITH TOPBAR}': 'b',
    '\N{LATIN CAPITAL LETTER OPEN O}': 'O',
    '\N{LATIN CAPITAL LETTER C WITH HOOK}': 'C',
    '\N{LATIN SMALL LETTER C WITH HOOK}': 'c',
    '\N{LATIN CAPITAL LETTER AFRICAN D}': 'D',
    '\N{LATIN CAPITAL LETTER D WITH HOOK}': 'D',
    '\N{LATIN CAPITAL LETTER D WITH TOPBAR}': 'D',
    '\N{LATIN SMALL LETTER D WITH TOPBAR}': 'd',
    '\N{LATIN CAPITAL LETTER REVERSED E}': 'E',
    '\N{LATIN CAPITAL LETTER OPEN E}': 'E',
    '\N{LATIN CAPITAL LETTER F WITH HOOK}': 'F',
    '\N{LATIN SMALL LETTER F WITH HOOK}': 'f',
    '\N{LATIN CAPITAL LETTER G WITH HOOK}': 'G',
    '\N{LATIN SMALL LETTER HV}': 'hv',
    '\N{LATIN CAPITAL LETTER IOTA}': 'i',
    '\N{LATIN CAPITAL LETTER I WITH STROKE}': 'I',
    '\N{LATIN CAPITAL LETTER K WITH HOOK}': 'K',
    '\N{LATIN SMALL LETTER K WITH HOOK}': 'k',
    '\N{LATIN SMALL LETTER L WITH BAR}': 'l',
    '\N{LATIN CAPITAL LETTER N WITH LEFT HOOK}': 'N',
    '\N{LATIN SMALL LETTER N WITH LONG RIGHT LEG}': 'N',
    '\N{LATIN CAPITAL LETTER O WITH MIDDLE TILDE}': 'O',
    '\N{LATIN CAPITAL LETTER OI}': 'OI',
    '\N{LATIN SMALL LETTER OI}': 'oi',
    '\N{LATIN CAPITAL LETTER P WITH HOOK}': 'P',
    '\N{LATIN SMALL LETTER P WITH HOOK}': 'p',
    '\N{LATIN CAPITAL LETTER ESH}': 'SH',
    '\N{LATIN SMALL LETTER T WITH PALATAL HOOK}': 't',
    '\N{LATIN CAPITAL LETTER T WITH HOOK}': 'T',
    '\N{LATIN SMALL LETTER T WITH HOOK}': 't',
    '\N{LATIN CAPITAL LETTER T WITH RETROFLEX HOOK}': 'T',
    '\N{LATIN CAPITAL LETTER V WITH HOOK}': 'V',
    '\N{LATIN CAPITAL LETTER Y WITH HOOK}': 'Y',
    '\N{LATIN SMALL LETTER Y WITH HOOK}': 'y',
    '\N{LATIN CAPITAL LETTER Z WITH STROKE}': 'Z',
    '\N{LATIN SMALL LETTER Z WITH STROKE}': 'z',
    '\N{LATIN CAPITAL LETTER EZH}': 'S',
    '\N{LATIN SMALL LETTER EZH WITH TAIL}': 's',
    '\N{LATIN LETTER WYNN}': 'w',
    '\N{LATIN CAPITAL LETTER AE WITH MACRON}': 'AE',
    '\N{LATIN SMALL LETTER AE WITH MACRON}': 'ae',
    '\N{LATIN CAPITAL LETTER G WITH STROKE}': 'G',
    '\N{LATIN SMALL LETTER G WITH STROKE}': 'g',
    '\N{LATIN CAPITAL LETTER EZH WITH CARON}': 'S',
    '\N{LATIN SMALL LETTER EZH WITH CARON}': 's',
    '\N{LATIN CAPITAL LETTER HWAIR}': 'HW',
    '\N{LATIN CAPITAL LETTER WYNN}': 'W',
    '\N{LATIN CAPITAL LETTER AE WITH ACUTE}': 'AE',
    '\N{LATIN SMALL LETTER AE WITH ACUTE}': 'AE',
    '\N{LATIN SMALL LETTER O WITH STROKE AND ACUTE}': 'o',
    '\N{LATIN CAPITAL LETTER YOGH}': 'J',
    '\N{LATIN SMALL LETTER YOGH}': 'j',
    '\N{LATIN CAPITAL LETTER N WITH LONG RIGHT LEG}': 'N',
    '\N{LATIN SMALL LETTER D WITH CURL}': 'd',
    '\N{LATIN CAPITAL LETTER OU}': 'OU',
    '\N{LATIN SMALL LETTER OU}': 'ou',
    '\N{LATIN CAPITAL LETTER Z WITH HOOK}': 'Z',
    '\N{LATIN SMALL LETTER Z WITH HOOK}': 'z',
    '\N{LATIN SMALL LETTER L WITH CURL}': 'l',
    '\N{LATIN SMALL LETTER N WITH CURL}': 'n',
    '\N{LATIN SMALL LETTER T WITH CURL}': 't',
    '\N{LATIN SMALL LETTER DOTLESS J}': 'j',
    '\N{LATIN SMALL LETTER DB DIGRAPH}': 'db',
    '\N{LATIN SMALL LETTER QP DIGRAPH}': 'qp',
    '\N{LATIN CAPITAL LETTER A WITH STROKE}': 'A',
    '\N{LATIN CAPITAL LETTER C WITH STROKE}': 'C',
    '\N{LATIN SMALL LETTER C WITH STROKE}': 'C',
    '\N{LATIN CAPITAL LETTER L WITH BAR}': 'L',
    '\N{LATIN CAPITAL LETTER T WITH DIAGONAL STROKE}': 'T',
    '\N{LATIN SMALL LETTER S WITH SWASH TAIL}': 'S',
    '\N{LATIN SMALL LETTER Z WITH SWASH TAIL}': 'Z',
    '\N{LATIN SMALL LETTER B WITH HOOK}': 'b',
    '\N{LATIN SMALL LETTER OPEN O}': 'o',
    '\N{LATIN SMALL LETTER C WITH CURL}': 'c',
    '\N{LATIN SMALL LETTER D WITH TAIL}': 'd',
    '\N{LATIN SMALL LETTER D WITH HOOK}': 'd',
    '\N{LATIN SMALL LETTER OPEN E}': 'e',
    '\N{LATIN SMALL LETTER DOTLESS J WITH STROKE}': 'j',
    '\N{LATIN SMALL LETTER G WITH HOOK}': 'g',
    '\N{LATIN SMALL LETTER SCRIPT G}': 'g',
    '\N{LATIN LETTER SMALL CAPITAL G}': 'G',
    '\N{LATIN SMALL LETTER H WITH HOOK}': 'h',
    '\N{LATIN SMALL LETTER HENG WITH HOOK}': 'h',
    '\N{LATIN SMALL LETTER I WITH STROKE}': 'i',
    '\N{LATIN LETTER SMALL CAPITAL I}': 'I',
    '\N{LATIN SMALL LETTER L WITH MIDDLE TILDE}': 'L',
    '\N{LATIN SMALL LETTER L WITH BELT}': 'L',
    '\N{LATIN SMALL LETTER L WITH RETROFLEX HOOK}': 'L',
    '\N{LATIN SMALL LETTER M WITH HOOK}': 'm',
    '\N{LATIN SMALL LETTER N WITH LEFT HOOK}': 'n',
    '\N{LATIN SMALL LETTER N WITH RETROFLEX HOOK}': 'n',
    '\N{LATIN LETTER SMALL CAPITAL N}': 'N',
    '\N{LATIN SMALL LETTER BARRED O}': 'o',
    '\N{LATIN LETTER SMALL CAPITAL OE}': 'OE',
    '\N{LATIN SMALL LETTER R WITH LONG LEG}': 'r',
    '\N{LATIN SMALL LETTER R WITH TAIL}': 'r',
    '\N{LATIN SMALL LETTER R WITH FISHHOOK}': 'r',
    '\N{LATIN LETTER SMALL CAPITAL R}': 'R',
    '\N{LATIN SMALL LETTER S WITH HOOK}': 's',
    '\N{LATIN SMALL LETTER ESH}': 'sh',
    '\N{LATIN SMALL LETTER DOTLESS J WITH STROKE AND HOOK}': 'j',
    '\N{LATIN SMALL LETTER ESH WITH CURL}': 'sh',
    '\N{LATIN SMALL LETTER T WITH RETROFLEX HOOK}': 't',
    '\N{LATIN SMALL LETTER U BAR}': 'u',
    '\N{LATIN SMALL LETTER V WITH HOOK}': 'v',
    '\N{LATIN LETTER SMALL CAPITAL Y}': 'Y',
    '\N{LATIN SMALL LETTER Z WITH RETROFLEX HOOK}': 'z',
    '\N{LATIN SMALL LETTER Z WITH CURL}': 'z',
    '\N{LATIN SMALL LETTER EZH}': 's',
    '\N{LATIN SMALL LETTER EZH WITH CURL}': 's',
    '\N{LATIN LETTER STRETCHED C}': 'c',
    '\N{LATIN LETTER SMALL CAPITAL B}': 'B',
    '\N{LATIN SMALL LETTER CLOSED OPEN E}': 'e',
    '\N{LATIN LETTER SMALL CAPITAL G WITH HOOK}': 'G',
    '\N{LATIN LETTER SMALL CAPITAL H}': 'H',
    '\N{LATIN SMALL LETTER J WITH CROSSED-TAIL}': 'j',
    '\N{LATIN LETTER SMALL CAPITAL L}': 'L',
    '\N{LATIN SMALL LETTER Q WITH HOOK}': 'q',
    '\N{LATIN LETTER SMALL CAPITAL A}': 'A',
    '\N{LATIN LETTER SMALL CAPITAL AE}': 'AE',
    '\N{LATIN LETTER SMALL CAPITAL BARRED B}': 'B',
    '\N{LATIN LETTER SMALL CAPITAL C}': 'C',
    '\N{LATIN LETTER SMALL CAPITAL D}': 'D',
    '\N{LATIN LETTER SMALL CAPITAL ETH}': 'D',
    '\N{LATIN LETTER SMALL CAPITAL E}': 'E',
    '\N{LATIN LETTER SMALL CAPITAL J}': 'J',
    '\N{LATIN LETTER SMALL CAPITAL K}': 'K',
    '\N{LATIN LETTER SMALL CAPITAL L WITH STROKE}': 'L',
    '\N{LATIN LETTER SMALL CAPITAL M}': 'M',
    # u'\N{LATIN LETTER SMALL CAPITAL REVERSED N}': u'',
    '\N{LATIN LETTER SMALL CAPITAL O}': 'O',
    '\N{LATIN LETTER SMALL CAPITAL OPEN O}': 'O',
    '\N{LATIN LETTER SMALL CAPITAL OU}': 'OU',
    # u'\N{LATIN SMALL LETTER TOP HALF O}': u'',
    # u'\N{LATIN SMALL LETTER BOTTOM HALF O}': u'',
    '\N{LATIN LETTER SMALL CAPITAL P}': 'P',
    # u'\N{LATIN LETTER SMALL CAPITAL REVERSED R}': u'',
    # u'\N{LATIN LETTER SMALL CAPITAL TURNED R}': u'',
    '\N{LATIN LETTER SMALL CAPITAL T}': 'T',
    '\N{LATIN LETTER SMALL CAPITAL U}': 'U',
    # u'\N{LATIN SMALL LETTER SIDEWAYS U}': u'',
    # u'\N{LATIN SMALL LETTER SIDEWAYS DIAERESIZED U}': u'',
    # u'\N{LATIN SMALL LETTER SIDEWAYS TURNED M}': u'',
    '\N{LATIN LETTER SMALL CAPITAL V}': 'V',
    '\N{LATIN LETTER SMALL CAPITAL W}': 'W',
    '\N{LATIN LETTER SMALL CAPITAL Z}': '',
    '\N{LATIN LETTER SMALL CAPITAL EZH}': 'S',
    # u'\N{LATIN LETTER VOICED LARYNGEAL SPIRANT}': u'',
    # u'\N{LATIN LETTER AIN}': u'',
    '\N{LATIN SMALL LETTER UE}': 'ue',
    '\N{LATIN SMALL LETTER B WITH MIDDLE TILDE}': 'b',
    '\N{LATIN SMALL LETTER D WITH MIDDLE TILDE}': 'd',
    '\N{LATIN SMALL LETTER F WITH MIDDLE TILDE}': 'f',
    '\N{LATIN SMALL LETTER M WITH MIDDLE TILDE}': 'm',
    '\N{LATIN SMALL LETTER N WITH MIDDLE TILDE}': 'n',
    '\N{LATIN SMALL LETTER P WITH MIDDLE TILDE}': 'p',
    '\N{LATIN SMALL LETTER R WITH MIDDLE TILDE}': 'r',
    '\N{LATIN SMALL LETTER R WITH FISHHOOK AND MIDDLE TILDE}': 'r',
    '\N{LATIN SMALL LETTER S WITH MIDDLE TILDE}': 's',
    '\N{LATIN SMALL LETTER T WITH MIDDLE TILDE}': 't',
    '\N{LATIN SMALL LETTER Z WITH MIDDLE TILDE}': 'z',
    # u'\N{LATIN SMALL LETTER TURNED G}': u'',
    # u'\N{LATIN SMALL LETTER INSULAR G}': u'',
    '\N{LATIN SMALL LETTER TH WITH STRIKETHROUGH}': 'th',
    '\N{LATIN SMALL CAPITAL LETTER I WITH STROKE}': 'I',
    # u'\N{LATIN SMALL LETTER IOTA WITH STROKE}': u'',
    '\N{LATIN SMALL LETTER P WITH STROKE}': 'p',
    '\N{LATIN SMALL CAPITAL LETTER U WITH STROKE}': 'U',
    # u'\N{LATIN SMALL LETTER UPSILON WITH STROKE}': u'',
    '\N{LATIN SMALL LETTER B WITH PALATAL HOOK}': 'b',
    '\N{LATIN SMALL LETTER D WITH PALATAL HOOK}': 'd',
    '\N{LATIN SMALL LETTER F WITH PALATAL HOOK}': 'f',
    '\N{LATIN SMALL LETTER G WITH PALATAL HOOK}': 'g',
    '\N{LATIN SMALL LETTER K WITH PALATAL HOOK}': 'k',
    '\N{LATIN SMALL LETTER L WITH PALATAL HOOK}': 'l',
    '\N{LATIN SMALL LETTER M WITH PALATAL HOOK}': 'm',
    '\N{LATIN SMALL LETTER N WITH PALATAL HOOK}': 'n',
    '\N{LATIN SMALL LETTER P WITH PALATAL HOOK}': 'p',
    '\N{LATIN SMALL LETTER R WITH PALATAL HOOK}': 'r',
    '\N{LATIN SMALL LETTER S WITH PALATAL HOOK}': 's',
    '\N{LATIN SMALL LETTER ESH WITH PALATAL HOOK}': 'sh',
    '\N{LATIN SMALL LETTER V WITH PALATAL HOOK}': 'v',
    '\N{LATIN SMALL LETTER X WITH PALATAL HOOK}': 'x',
    '\N{LATIN SMALL LETTER Z WITH PALATAL HOOK}': 'z',
    '\N{LATIN SMALL LETTER A WITH RETROFLEX HOOK}': 'a',
    # u'\N{LATIN SMALL LETTER ALPHA WITH RETROFLEX HOOK}': u'',
    '\N{LATIN SMALL LETTER D WITH HOOK AND TAIL}': 'd',
    '\N{LATIN SMALL LETTER E WITH RETROFLEX HOOK}': 'e',
    '\N{LATIN SMALL LETTER OPEN E WITH RETROFLEX HOOK}': 'e',
    '\N{LATIN SMALL LETTER REVERSED OPEN E WITH RETROFLEX HOOK}': 'e',
    # u'\N{LATIN SMALL LETTER SCHWA WITH RETROFLEX HOOK}': u'',
    '\N{LATIN SMALL LETTER I WITH RETROFLEX HOOK}': 'i',
    '\N{LATIN SMALL LETTER OPEN O WITH RETROFLEX HOOK}': 'o',
    '\N{LATIN SMALL LETTER ESH WITH RETROFLEX HOOK}': 'sh',
    '\N{LATIN SMALL LETTER U WITH RETROFLEX HOOK}': 'u',
    '\N{LATIN SMALL LETTER EZH WITH RETROFLEX HOOK}': 's',
    # u'\N{LATIN SUBSCRIPT SMALL LETTER SCHWA}': u'',
    # u'\N{LATIN CROSS}': u''
}

# Additional ones; see "man uni2ascii"
UNI2ASCII_CONVERSIONS = {
    '\N{NO-BREAK SPACE}': ' ',
    '\N{LEFT-POINTING DOUBLE ANGLE QUOTATION MARK}': '"',
    '\N{SOFT HYPHEN}': '',
    '\N{RIGHT-POINTING DOUBLE ANGLE QUOTATION MARK}': '"',
    '\N{ETHIOPIC WORDSPACE}': ' ',
    '\N{OGHAM SPACE MARK}': ' ',
    '\N{EN QUAD}': ' ',
    '\N{EM QUAD}': ' ',
    '\N{EN SPACE}': ' ',
    '\N{EM SPACE}': ' ',
    '\N{THREE-PER-EM SPACE}': ' ',
    '\N{FOUR-PER-EM SPACE}': ' ',
    '\N{SIX-PER-EM SPACE}': ' ',
    '\N{FIGURE SPACE}': ' ',
    '\N{PUNCTUATION SPACE}': ' ',
    '\N{THIN SPACE}': ' ',
    '\N{HAIR SPACE}': ' ',
    '\N{ZERO WIDTH SPACE}': ' ',
    '\N{ZERO WIDTH NO-BREAK SPACE}': ' ',
    '\N{HYPHEN}': '-',
    '\N{NON-BREAKING HYPHEN}': '-',
    '\N{FIGURE DASH}': '-',
    '\N{EN DASH}': '-',
    '\N{EM DASH}': '-',
    '\N{LEFT SINGLE QUOTATION MARK}': '`',
    '\N{RIGHT SINGLE QUOTATION MARK}': "'",
    '\N{SINGLE LOW-9 QUOTATION MARK}': '`',
    '\N{SINGLE HIGH-REVERSED-9 QUOTATION MARK}': '`',
    '\N{LEFT DOUBLE QUOTATION MARK}': '"',
    '\N{RIGHT DOUBLE QUOTATION MARK}': '"',
    '\N{DOUBLE LOW-9 QUOTATION MARK}': '"',
    '\N{DOUBLE HIGH-REVERSED-9 QUOTATION MARK}': '"',
    '\N{SINGLE LEFT-POINTING ANGLE QUOTATION MARK}': '`',
    '\N{SINGLE RIGHT-POINTING ANGLE QUOTATION MARK}': "'",
    '\N{LOW ASTERISK}': '*',
    '\N{MINUS SIGN}': '-',
    '\N{ASTERISK OPERATOR}': '*',
    '\N{BOX DRAWINGS LIGHT HORIZONTAL}': '-',
    '\N{BOX DRAWINGS HEAVY HORIZONTAL}': '-',
    '\N{BOX DRAWINGS LIGHT VERTICAL}': '|',
    '\N{BOX DRAWINGS HEAVY VERTICAL}': '|',
    '\N{HEAVY ASTERISK}': '*',
    '\N{HEAVY DOUBLE TURNED COMMA QUOTATION MARK ORNAMENT}': '"',
    '\N{HEAVY DOUBLE COMMA QUOTATION MARK ORNAMENT}': '"',
    '\N{IDEOGRAPHIC SPACE}': ' ',
    '\N{SMALL AMPERSAND}': '&',
    '\N{SMALL ASTERISK}': '*',
    '\N{SMALL PLUS SIGN}': '+',
    '\N{CENT SIGN}': 'cent',
    '\N{POUND SIGN}': 'pound',
    '\N{YEN SIGN}': 'yen',
    '\N{COPYRIGHT SIGN}': '(c)',
    '\N{REGISTERED SIGN}': '(R)',
    '\N{VULGAR FRACTION ONE QUARTER}': '1/4',
    '\N{VULGAR FRACTION ONE HALF}': '1/2',
    '\N{VULGAR FRACTION THREE QUARTERS}': '3/4',
    '\N{LATIN SMALL LETTER SHARP S}': 'ss',
    '\N{LATIN CAPITAL LIGATURE IJ}': 'IJ',
    '\N{LATIN SMALL LIGATURE IJ}': 'ij',
    '\N{LATIN CAPITAL LIGATURE OE}': 'OE',
    '\N{LATIN SMALL LIGATURE oe}': 'oe',
    '\N{LATIN CAPITAL LETTER DZ}': 'DZ',
    '\N{LATIN CAPITAL LETTER DZ WITH CARON}': 'DZ',
    '\N{LATIN CAPITAL LETTER D WITH SMALL LETTER Z}': 'Dz',
    '\N{LATIN CAPITAL LETTER D WITH SMALL LETTER Z WITH CARON}': 'Dz',
    '\N{LATIN SMALL LETTER DZ}': 'dz',
    '\N{LATIN SMALL LETTER TS DIGRAPH}': 'ts',
    '\N{HORIZONTAL ELLIPSIS}': '...',
    '\N{MIDLINE HORIZONTAL ELLIPSIS}': '...',
    '\N{LEFTWARDS ARROW}': '<-',
    '\N{RIGHTWARDS ARROW}': '->',
    '\N{LEFTWARDS DOUBLE ARROW}': '<=',
    '\N{RIGHTWARDS DOUBLE ARROW}': '=>',
}

# More from "man uni2ascii", in a different category.
EXTRA_CHARACTERS = {
    '\N{ACUTE ACCENT}': "'",
    '\N{BROKEN BAR}': '|',
    '\N{CENT SIGN}': ' cents ',
    '\N{COPYRIGHT SIGN}': '(C)',
    '\N{CURRENCY SIGN}': ' currency ',
    '\N{DEGREE SIGN}': ' degrees ',
    '\N{DIVISION SIGN}': '/',
    '\N{INVERTED EXCLAMATION MARK}': '!',
    '\N{INVERTED QUESTION MARK}': '?',
    '\N{MACRON}': '_',
    '\N{MICRO SIGN}': 'micro',
    '\N{MIDDLE DOT}': '*',
    '\N{MULTIPLICATION SIGN}': '*',
    '\N{NOT SIGN}': 'not',
    '\N{PILCROW SIGN}': 'paragraph',
    '\N{PLUS-MINUS SIGN}': '+/-',
    '\N{POUND SIGN}': 'pound',
    '\N{REGISTERED SIGN}': '(R)',
    '\N{SECTION SIGN}': 'section',
    '\N{SOFT HYPHEN}': '',
    '\N{SUPERSCRIPT ONE}': '^1',
    '\N{SUPERSCRIPT THREE}': '^3',
    '\N{SUPERSCRIPT TWO}': '^2',
    '\N{VULGAR FRACTION ONE HALF}': '1/2',
    '\N{VULGAR FRACTION ONE QUARTER}': '1/4',
    '\N{VULGAR FRACTION THREE QUARTERS}': '3/4',
    '\N{YEN SIGN}': 'yen'
}
FG_HACKS = {
    '\u0082': '',  # "break permitted here" symbol
    '\u2022': '*',  # Bullet
}


def build_dictionary():
    'Return the translation dictionary.'
    d = dict()
    # First do what can be done automatically
    for i in range(0xffff):
        u = chr(i)
        try:
            n = unicodedata.name(u)
            if n.startswith('LATIN '):
                k = unicodedata.normalize('NFKD', u).encode('ASCII', 'ignore')
                if k:
                    d[i] = str(k)  # i=ord(u)
        except ValueError:
            pass
    # Next, add some by-hand ones (overlap possible, so order matters)
    for m in [EXTRA_LATIN_NAMES, EXTRA_CHARACTERS,
              UNI2ASCII_CONVERSIONS, FG_HACKS]:
        for i in m:
            try:
                d[ord(i)] = str(m[i])
            except Exception:
                pass
    return d


udict = build_dictionary()


def convert(string):
    return string.translate(udict)


def coroutine(func):
    def start(*argz, **kwz):
        cr = func(*argz, **kwz)
        next(cr)
        return cr
    return start


@coroutine
def co_filter(drain, in_enc='utf-8', out_enc='ascii'):
    bs = None
    while True:
        chunk = (yield bs)
        bs = drain(convert(str(chunk)).encode('utf-8'))


def uc_filter(sin, sout, bs=8192, in_enc='utf-8', out_enc='ascii'):
    sout = co_filter(sout.write, in_enc, out_enc)
    while True:
        dta = sin.read(bs)
        if not dta:
            break
        else:
            sout.send(dta)


if __name__ == '__main__':
    from optparse import OptionParser
    parser = OptionParser(
        usage='%prog [options]',
        description='utf8 stdin -> ascii stdout'
    )
    parser.add_option(
        '-s',
        '--src-enc',
        action='store',
        type='str',
        dest='src_enc',
        metavar='ENC',
        default='utf-8',
        help='source encoding (utf-8)'
    )
    parser.add_option(
        '-d',
        '--dst-enc',
        action='store',
        type='str',
        dest='dst_enc',
        metavar='ENC',
        default='ascii',
        help='destination encoding (ascii)'
    )
    parser.add_option(
        '-c',
        '--chunk',
        action='store',
        type='int',
        dest='bs',
        metavar='BYTES',
        default=8192,
        help='read/write in chunks of a given size (8192)'
    )
    optz, arguments = parser.parse_args()
    if arguments:
        parser.error('Only stdin -> stdout conversion suported')

    uc_filter(sys.stdin, sys.stdout, bs=optz.bs,
              in_enc=optz.src_enc, out_enc=optz.dst_enc)
