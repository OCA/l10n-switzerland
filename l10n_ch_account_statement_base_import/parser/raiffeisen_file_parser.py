# -*- coding: utf-8 -*-
###############################################################################
#
#   Authors: David Wulliamoz <dwulliamoz@compassion.ch>
#            Emanuel Cino <ecino@compassion.ch>
#   Copyright 2013-2014 Compassion CH
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

from datetime import datetime
import tempfile
import csv
import re
from account_statement_base_import.parser.file_parser import FileParser

from openerp.osv import orm
from openerp.tools.translate import _

import logging
logger = logging.getLogger(__name__)


def float_or_zero(val):
    """ Conversion function used to manage
    empty string into float usecase"""
    return float(val) if val else 0.0


class RaiffeisenFileParser(FileParser):

    def __init__(self, parse_name, ftype='csv', extra_fields=None,
                 header=None, **kwargs):
        """
        :param char: parse_name: The name of the parser
        :param char: ftype: extension of the file
        :param dict: extra_fields: extra fields to add to the conversion dict.
        :param list: header : specify header fields if the csv file
        has no header
        """

        super(RaiffeisenFileParser, self).__init__(parse_name, **kwargs)
        self.conversion_dict = {
            'Text': unicode,
            'Booked At': datetime,
            'Credit/Debit Amount': float_or_zero,
        }
        self.keys_to_validate = self.conversion_dict.keys()

    @classmethod
    def parser_for(cls, parser_name):
        """
        Used by the new_bank_statement_parser class factory. Return true if
        the providen name is raiffeisen_csvparser
        """
        return parser_name == 'raiffeisen_csvparser'

    def get_st_line_vals(self, line, *args, **kwargs):
        """
        This method must return a dict of vals that can be passed to create
        method of statement line in order to record it.
            :param:  line: a dict of vals that represent a line of
                           result_row_list
            :return: dict of values to give to the create method of
                     statement line,
        """
        res = {
            'name': line.get("Text"),
            'date': line.get("Booked At", datetime.now().date()),
            'amount': line.get("Credit/Debit Amount", 0.0),
            'ref': '/',
            'label': line.get("Text")
        }

        return res

    def _custom_format(self, *args, **kwargs):
        """
        The file format is in iso-8859-15, must be converted to
        utf-8 before parsing.
        """
        self.filebuffer = self.filebuffer.decode(
            'iso-8859-15').encode('utf-8')
        return True


class RaiffeisenDetailsFileParser(FileParser):

    def __init__(self, parse_name, ftype='csv', extra_fields=None,
                 header=None, **kwargs):
        """
        :param char: parse_name: The name of the parser
        :param char: ftype: extension of the file
        :param dict: extra_fields: extra fields to add to the conversion dict.
        :param list: header : specify header fields if the csv file
                              has no header
        """

        super(RaiffeisenDetailsFileParser, self).__init__(parse_name, **kwargs)
        self.conversion_dict = {
            'Text': unicode,
            'Booked At': datetime,
            'Credit/Debit Amount': float_or_zero,
        }
        self.keys_to_validate = self.conversion_dict.keys()

    @classmethod
    def parser_for(cls, parser_name):
        """
        Used by the new_bank_statement_parser class factory. Return true if
        the providen name is raiffeisen_details_csvparser
        """
        return parser_name == 'raiffeisen_details_csvparser'

    def _parse(self, *args, **kwargs):
        super(RaiffeisenDetailsFileParser, self)._parse(*args, **kwargs)
        first_balance = self.result_row_list[0].get('Balance').replace("'", '')
        first_amount = self.result_row_list[0].get(
            'Credit/Debit Amount').replace("'", '')
        self.balance_start = str(float(first_balance) - float(first_amount))

        i = 1
        while not self.result_row_list[-i].get('Balance'):
            i += 1
        self.balance_end = self.result_row_list[-i].get('Balance')

        return True

    def _post(self, *args, **kwargs):
        """
        Transform/drop sub rows to be consistent
        """
        cleanup_rows = []
        last_date = ''
        reported_text = ''
        reported_line = {}
        rate = 1
        currency = 'CHF'
        for row in self.result_row_list:
            if row.get('Booked At'):  # Main row
                rate = 1
                currency = 'CHF'
                reported_text = ''
                reported_line = {}
                last_date = row.get('Booked At')
                if row.get('Text').startswith(u'Crédit'):
                    reported_text = row.get('Text')[7:] + ' '
                elif row.get('Text').startswith(u'Virement postal'):
                    reported_text = row.get('Text')[16:] + ' '
                elif row.get('Text').startswith('Ordre collectif'):
                    rate = -1
                    reported_line = row
                    text_rate = row.get('Text').split(', taux de change ')
                    if len(text_rate) == 2:
                        rate *= float(text_rate[1])
                        currency = text_rate[0].split(' ')[-2]
                else:
                    cleanup_rows.append(row)
            else:  # Sub row
                if row.get('Text').startswith(u'Détails invisibles'):
                    if reported_line:
                        cleanup_rows.append(reported_line)
                        reported_line = {}
                    else:
                        continue
                elif reported_text or reported_line:
                    row['Booked At'] = last_date
                    name, amount = self._get_values(
                        row, currency=currency, rate=rate)
                    row['Text'] = reported_text + name
                    row['Credit/Debit Amount'] = amount
                    cleanup_rows.append(row)

        self.result_row_list = cleanup_rows

        return super(RaiffeisenDetailsFileParser, self)._post(*args, **kwargs)

    def get_st_line_vals(self, line, *args, **kwargs):
        """
        This method must return a dict of vals that can be passed to create
        method of statement line in order to record it.
            :param:  line: a dict of vals that represent a line of
                           result_row_list
            :return: dict of values to give to the create method of
                     statement line,
        """
        # We try to extract a BVR reference
        result = re.match('.*(\d{27}).*', line.get('Text'))
        ref = '/'
        if result and not line.get('Text').startswith(u'Crèdit'):
            ref = result.group(1)

        res = {
            'name': line.get("Text"),
            'date': line.get("Booked At", datetime.now().date()),
            'amount': line.get("Credit/Debit Amount", 0.0),
            'ref': ref,
            'label': line.get("Text")
        }

        return res

    def _custom_format(self, *args, **kwargs):
        """
        The file format is in iso-8859-15, must be converted
        to utf-8 before parsing.
        """
        self.filebuffer = self.filebuffer.decode('iso-8859-15').encode('utf-8')
        return True

    def _parse_csv(self):
        ''' UnicodeDictReader is not able to determine delimiter... '''
        csv_file = tempfile.NamedTemporaryFile()
        csv_file.write(self.filebuffer)
        csv_file.flush()
        with open(csv_file.name, 'rU') as fobj:
            reader = csv.DictReader(
                fobj, delimiter=';', fieldnames=self.fieldnames)
            rows = []
            for row in reader:
                rows.append(
                    dict([(key, unicode(value, 'utf-8'))
                         for key, value in row.iteritems()]))
            return rows

    def _get_values(self, line, currency='CHF', rate=1):
        name = ''
        amount = '0.0'
        vals = line.get('Text').split(' ' + currency + ' ')
        if len(vals) == 2:
            name = vals[0]
            amount = float(vals[1].replace("'", "")) * rate
        else:
            raise orm.except_orm('ParsingError',
                                 _('Unable to parse amount for ligne %s') %
                                 line.get('Text'))
        return name, str(amount)
