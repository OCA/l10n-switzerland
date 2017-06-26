##############################################################################
#
#    Swiss localization Direct Debit module for OpenERP
#    Copyright (C) 2015 Compassion (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from datetime import datetime, timedelta
from openerp import fields, exceptions, _
from openerp.tools import mod10r

# Mapping between Latin-1 to ascii characters, used for LSV.
LSV_LATIN1_TO_ASCII_MAPPING = {
    32: ' ', 33: '.', 34: '.', 35: '.', 36: '.', 37: '.', 38: '+', 39: "'",
    40: '(', 41: ')', 42: '.', 43: '+', 44: ',', 45: '-', 46: '.', 47: '/',
    48: '0', 49: '1', 50: '2', 51: '3', 52: '4', 53: '5', 54: '6', 55: '7',
    56: '8', 57: '9', 58: ':', 59: '.', 60: '.', 61: '.', 62: '.', 63: '?',
    64: '.', 65: 'A', 66: 'B', 67: 'C', 68: 'D', 69: 'E', 70: 'F', 71: 'G',
    72: 'H', 73: 'I', 74: 'J', 75: 'K', 76: 'L', 77: 'M', 78: 'N', 79: 'O',
    80: 'P', 81: 'Q', 82: 'R', 83: 'S', 84: 'T', 85: 'U', 86: 'V', 87: 'W',
    88: 'X', 89: 'Y', 90: 'Z', 91: '.', 92: '.', 93: '.', 94: '.', 95: '.',
    96: '.', 97: 'a', 98: 'b', 99: 'c', 100: 'd', 101: 'e', 102: 'f', 103: 'g',
    104: 'h', 105: 'i', 106: 'j', 107: 'k', 108: 'l', 109: 'm', 110: 'n',
    111: 'o', 112: 'p', 113: 'q', 114: 'r', 115: 's', 116: 't', 117: 'u',
    118: 'v', 119: 'w', 120: 'x', 121: 'y', 122: 'z', 123: '.', 124: '.',
    125: '.', 126: '.', 127: '.', 128: ' ', 129: ' ', 130: ' ', 131: ' ',
    132: ' ', 133: ' ', 134: ' ', 135: ' ', 136: ' ', 137: ' ', 138: ' ',
    139: ' ', 140: ' ', 141: ' ', 142: ' ', 143: ' ', 144: ' ', 145: ' ',
    146: ' ', 147: ' ', 148: ' ', 149: ' ', 150: ' ', 151: ' ', 152: ' ',
    153: ' ', 154: ' ', 155: ' ', 156: ' ', 157: ' ', 158: ' ', 159: ' ',
    160: '.', 161: '.', 162: '.', 163: '.', 164: '.', 165: '.', 166: '.',
    167: '.', 168: '.', 169: '.', 170: '.', 171: '.', 172: '.', 173: '.',
    174: '.', 175: '.', 176: '.', 177: '.', 178: '.', 179: '.', 180: '.',
    181: '.', 182: '.', 183: '.', 184: '.', 185: '.', 186: '.', 187: '.',
    188: '.', 189: '.', 190: '.', 191: '.', 192: 'A', 193: 'A', 194: 'A',
    195: 'A', 196: 'EA', 197: 'A', 198: 'EA', 199: 'C', 200: 'E', 201: 'E',
    202: 'E', 203: 'E', 204: 'I', 205: 'I', 206: 'I', 207: 'I', 208: '.',
    209: 'N', 210: 'O', 211: 'O', 212: 'O', 213: 'O', 214: 'EO', 215: '.',
    216: '.', 217: 'U', 218: 'U', 219: 'U', 220: 'EU', 221: 'Y', 222: '.',
    223: 'ss', 224: 'a', 225: 'a', 226: 'a', 227: 'a', 228: 'ea', 229: 'a',
    230: 'ea', 231: 'c', 232: 'e', 233: 'e', 234: 'e', 235: 'e', 236: 'i',
    237: 'i', 238: 'i', 239: 'i', 240: '.', 241: 'n', 242: 'o', 243: 'o',
    244: 'o', 245: 'o', 246: 'eo', 247: '.', 248: '.', 249: 'u', 250: 'u',
    251: 'u', 252: 'eu', 253: 'y', 254: '.', 255: 'y',
}


def complete_line(nb_char, line=''):
    ''' In LSV/DD files each field has a defined length.
        This way, lines have to be filled with spaces (or truncated).
    '''
    line = ''.join([LSV_LATIN1_TO_ASCII_MAPPING.get(ord(ch), ch)
                    for ch in line])
    if len(line) > nb_char:
        return line[:nb_char]

    return line.ljust(nb_char)


def get_treatment_date(prefered_type, line_mat_date, order_sched_date, name,
                       format='%Y%m%d'):
    ''' Returns appropriate date according to payment_order and
        payment_order_line data.
        Raises an error if treatment date is > today+30 or < today-10
    '''
    today = datetime.today()
    if prefered_type == 'due':
        requested_date = fields.Datetime.from_string(line_mat_date) \
            or today
    elif prefered_type == 'fixed':
        requested_date = fields.Datetime.from_string(order_sched_date) \
            or today
    elif prefered_type == 'now':
        requested_date = today
    else:
        raise exceptions.Warning('Preferred type not implemented')

    # Accepted dates are in range -90 to +90 days. We could go up
    # to +1 year, but we should be sure that we have less than
    # 1000 lines in payment order
    if requested_date > today + timedelta(days=90) \
            or requested_date < today - timedelta(days=90):
        raise exceptions.ValidationError(
            _('Incorrect treatment date: %s for line with '
              'ref %s') % (requested_date, name)
        )

    return requested_date.strftime(format)


def is_bvr_ref(ref):
    if not ref:
        return False  # Empty is not valid
    clean_ref = ref.replace(' ', '')
    if not clean_ref.isdigit() or len(clean_ref) > 27:
        return False
    clean_ref = clean_ref.rjust(27, '0')  # Add zeros to the left
    if not clean_ref == mod10r(clean_ref[0:26]):
        return False

    return True


def check_currency(line, properties):
    ''' Check that line currency is equal to dd export currency '''
    if not line.currency_id.name == properties.get('currency'):
        raise exceptions.ValidationError(
            _('Line with ref %s has %s currency and generated '
              'file %s (should be the same)') %
            (line.name, line.currency_id.name, properties.get(
                'currency', ''))
        )
