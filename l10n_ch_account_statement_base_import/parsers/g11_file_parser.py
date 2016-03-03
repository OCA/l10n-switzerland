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
import time
import logging
import uuid
from openerp import _

from .base_parser import BaseSwissParser

_logger = logging.getLogger(__name__)


class G11Parser(BaseSwissParser):
    """
    Parser for BVR DD type 2 Postfinance Statements
    (can be wrapped in a g11 file)
    """

    _ftype = 'g11'

    def __init__(self, data_file):
        """Constructor
        Splitting data_file in lines
        """

        super(G11Parser, self).__init__(data_file)
        self.lines = data_file.splitlines()
        self.reject_reason = {
            '01': _("Insufficient cover funds."),
            '02': _("Debtor protestation."),
            '03': _("Debtor’s account number and address do not match."),
            '04': _("Postal account closed."),
            '05': _("Postal account blocked/frozen."),
            '06': _("Postal account holder deceased."),
            '07': _("Postal account number non-existent.")
        }
        self.balance_end = 0.0

    def file_is_known(self):
        """Predicate the tells if the parser can parse the data file

        :return: True if file is supported
        :rtype: bool
        """

        return self.lines[-1][0:3] == '097'

    def _parse_currency_code(self):
        """Parse file currency ISO code

        :return: the currency ISO code of the file eg: CHF
        :rtype: string
        """

        return self.lines[-1][128:131]

    def _parse_statement_balance_end(self, line=None):
        """Parse file start and end balance

        :return: the file end balance
        :rtype: float
        """
        total_line = line or self.lines[-1]
        return ((float(total_line[45:57]) / 100) -
                (float(total_line[101:113]) / 100))

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
        for line in self.lines[:-1]:
            if line[0:3] != '097':
                ref = line[15:42]
                currency = line[42:45]
                amount = float(line[45:57]) / 100
                transaction_date = time.strftime(
                    '%Y-%m-%d', time.strptime(line[108:116], '%Y%m%d'))
                # commission = float(line[141:147]) / 100
                note = ''

                if line[0:3] == '084':
                    # Fail / Debit record
                    reject_code = line[128:130]
                    if reject_code == '02':
                        # Debit record
                        amount *= -1
                        note = self.reject_reason[reject_code]
                    else:
                        # Failed transactions. Get the error reason and
                        # put it on the OBI field.
                        note = self.reject_reason[
                            reject_code] + '\n' + _(
                                "Amount to debit was %s %f") % (
                                    currency, amount)
                        amount = 0.0

                # Add information to OBI if the transaction is a test.
                if line[5] == '3':
                    note = _("-- Test transaction --") + '\n' + note

                transactions.append({
                    'name': '/',
                    'ref': ref,
                    'unique_import_id': str(uuid.uuid4()),
                    'amount': amount,
                    'date': transaction_date,
                    'note': note,
                })
            else:
                self.balance_end += self._parse_statement_balance_end(line)
        return transactions

    def validate(self):
        """Validate the bank statement
        :param total_line: Last line in the g11 file. Beginning with '097'
        :return: Boolean
        """

        total_line = self.lines[-1]
        transactions = 0
        transactions += int(
            total_line[57:69]) + int(
                total_line[89:101]) + int(
                    total_line[113:125])
        return (len(self.statements[0]['transactions']) == transactions)

    def _parse_statement_date(self):
        """Parse file statement date
        :return: A date usable by Odoo in write or create dict
        """
        date = self.lines[0][92:100]
        fdate = date[0:4] + '-' + date[4:6] + '-' + date[6:]
        return fdate

    def _parse(self):
        """
        Launch the parsing through The g11 file.
        """

        self.currency_code = self._parse_currency_code()
        self.balance_end = self._parse_statement_balance_end()
        statement = {
            'balance_start': 0.0,
            'date': self._parse_statement_date(),
            'attachments': [('Statement File',
                             self.data_file.encode('base64'))],
            'transactions': self._parse_transactions(),
            'balance_end_real': self.balance_end
        }
        self.statements.append(statement)
        return self.validate()
