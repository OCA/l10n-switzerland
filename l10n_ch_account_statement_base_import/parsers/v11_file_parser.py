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
from openerp import fields

from .base_parser import BaseSwissParser

_logger = logging.getLogger(__name__)


class V11Parser(BaseSwissParser):
    """
    Parser for BVR DD type 2 Postfinance Statements
    (can be wrapped in a g11 file)
    """

    _ftype = 'v11'

    def __init__(self, data_file):
        """Constructor
        Splitting data_file in lines
        """

        super(V11Parser, self).__init__(data_file)
        self.lines = data_file.splitlines()
        self.balance_end = 0.0
        self.number_transaction = 0

    def file_is_known(self):
        """Predicate the tells if the parser can parse the data file

        :return: True if file is supported
        :rtype: bool
        """

        return (self.lines[-1][0:3] in ('999', '995'))

    def _parse_currency_code(self):
        """Parse file currency ISO code

        :return: the currency ISO code of the file eg: CHF
        :rtype: string
        """

        return 'CHF'

    def _parse_stmt_balance_num_trans(self):
        """Parse file start and end balance

        :return: the file end balance
        :rtype: float
        """

        total_line = self.lines[-1]
        return (float(total_line[39:51])/100), int(total_line[51:63])

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

        id = 0
        transactions = []
        for line in self.lines[:-1]:
            if line[0:3] in ('999', '995'):
                # Total line : addition the amount to the balance_end
                self.balance_end += (float(line[39:51]) / 100)
                self.number_transaction += int(line[51:63])
            else:
                ref = line[12:39]
                amount = float(line[39:49]) / 100
                format_date = time.strftime(
                    '%Y-%m-%d', time.strptime(line[71:77], '%y%m%d'))
                cost = float(line[96:100]) / 100  # not used

                if line[2] == '5':
                    amount *= -1
                    cost *= -1

                transactions.append({
                    'name': '/',
                    'ref': ref,
                    'unique_import_id': str(uuid.uuid4()),
                    'amount': amount,
                    'date': format_date,
                })
                id += 1
        return transactions

    def validate(self):
        """Validate the bank statement
        :param total_line: Last line in the g11 file. Beginning with '097'
        :return: Boolean
        """

        return (len(self.statements[0]['transactions']) ==
                self.number_transaction)

    def _parse_statement_date(self):
        """Parse file statement date
        :return: A date usable by Odoo in write or create dict
        """
        year = fields.Date.today()[:4]
        date = self.lines[0][61:65]
        fdate = year + '-' + date[0:2] + '-' + date[2:]
        return fdate

    def _parse(self):
        """
        Launch the parsing through The g11 file.
        """

        self.currency_code = self._parse_currency_code()
        self.balance_end, self.number_transaction = \
            self._parse_stmt_balance_num_trans()
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
