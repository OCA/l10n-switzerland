# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Steve Ferry
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import datetime
import logging
import csv
import re
import uuid
from openerp import fields, exceptions, _

from .base_parser import BaseSwissParser
_logger = logging.getLogger(__name__)


class RaffeisenCSVParser(BaseSwissParser):
    """
    Parser for Raffaisen CSV Statements
    """

    _ftype = 'raffeisen_csv'

    def __init__(self, data_file):
        """Constructor
        Splitting data_file in lines and fill a dict with key - value from the
        csv file
        """
        super(RaffeisenCSVParser, self).__init__(data_file)
        rows = []
        reader = csv.DictReader(self.data_file.splitlines(), delimiter=';')

        for row in reader:
            rows.append(
                dict([(key, value)
                      for key, value in row.iteritems()]))
        self.rows = rows

    def file_is_known(self):
        """Predicate the tells if the parser can parse the data file

        :return: True if file is supported
        :rtype: bool
        """

        return ('Booked At' in self.rows[0] and 'Text' in self.rows[0])

    def _parse_currency_code(self):
        """Parse file currency ISO code

        :return: the currency ISO code of the file eg: CHF
        :rtype: string
        """

        return 'CHF'

    def _parse_statement_balance(self):
        """Parse file start and end balance

        :return: Tuple with the file start and end balance
        :rtype: float
        """

        first_balance = float(self.rows[0].get('Balance').replace("'", ''))
        first_amount = float(self.rows[0].get(
            'Credit/Debit Amount').replace("'", ''))
        balance_start = float(first_balance - first_amount)

        i = 1
        while not self.rows[-i].get('Balance'):
            i += 1
        balance_end = float(self.rows[-i].get('Balance'))

        return balance_start, balance_end

    def _parse_transactions(self):
        """Parse bank statement lines from file
        list of dict containing :
            - 'name': string (e.g: 'KBC-INVESTERINGSKREDIET 787-5562831-01')
            - 'date': date
            - 'amount': float
            - 'unique_import_id': string
            -o 'account_number': string
                Will be used to find/create the res.partner.bank in odoo
            -o 'note': string
            -o 'partner_name': string
            -o 'ref': string

        :return: a list of transactions
        :rtype: list
        """

        transactions = []
        id = 0
        for row in self.rows:
            transactions.append(self.get_st_line_vals(row, id))
            id += 1

        return transactions

    def _get_values(self, line, currency='CHF', rate=1):
        name = ''
        amount = '0.0'
        vals = line.get('Text').rsplit(' ' + currency + ' ', 1)
        if len(vals) == 2:
            name = vals[0]
            amount = float(vals[1].replace("'", "")) * rate
        else:
            raise exceptions.Warning(
                'ParsingError', _('Unable to parse amount for line %s') %
                line.get('Text'))
        return name, str(amount)

    def get_st_line_vals(self, line, id):
        """
        This method must return a dict of vals that can be passed to create
        method of statement line in order to record it.
            :param:  line: a dict of vals that represent a line of
                           result_row_list
            :return: dict of values to give to the create method of
                     statement line,
        """

        # We try to extract a BVR reference
        result = re.match(r'.*(\d{27}).*', line.get('Text'))
        ref = '/'
        test = 'Crèdit'.decode('iso-8859-15').encode('utf8')
        if result and not line.get('Text').startswith(test):
            ref = result.group(1)

        date = fields.Date.from_string(line.get("Booked At",
                                                datetime.date.today()))
        res = {
            'name': line.get("Text"),
            'date': line.get("Booked At", date),
            'amount': line.get("Credit/Debit Amount", 0.0),
            'ref': ref,
            'unique_import_id': str(uuid.uuid4())
        }

        return res

    def cleanup_rows(self, rows):
        """
        Clean up rows to remove useless details for the statement line
        """

        cleanup_rows = []
        last_date = ''
        reported_text = ''
        reported_line = {}
        rate = 1
        currency = 'CHF'
        for row in rows:
            if row.get('Booked At'):  # Main row
                rate = 1
                currency = 'CHF'
                reported_text = ''
                reported_line = {}
                last_date = row.get('Booked At')
                if row.get('Text').startswith('Crédit'):
                    reported_text = row.get('Text')[7:] + ' '
                elif row.get('Text').startswith('Virement postal'):
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
                if row.get('Text').startswith('Détails invisibles'):
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

        return cleanup_rows

    def _parse_statement_date(self):
        """Parse file statement date
        :return: A date usable by Odoo in write or create dict
        """

        return fields.Date.today()

    def _parse(self):
        """
        Launch the parsing through the Raffaisen csv file.
        """

        balance_start, balance_end = self._parse_statement_balance()

        self.rows = self.cleanup_rows(self.rows)
        self.currency_code = self._parse_currency_code()
        statement = {
            'balance_start': balance_start,
            'date': self._parse_statement_date(),
            'attachments': [('Statement File',
                             self.data_file.encode('base64'))],
            'transactions': self._parse_transactions(),
            'balance_end_real': balance_end
        }
        self.statements.append(statement)
        return True
