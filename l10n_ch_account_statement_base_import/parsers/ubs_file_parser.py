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
import uuid
from openerp import fields
from .base_parser import BaseSwissParser

_logger = logging.getLogger(__name__)


def float_or_zero(val):
    """ Conversion function used to manage
    empty string into float usecase"""

    val = val.replace("'", "")
    return float(val) if val else 0.0


def format_date(val):
    return datetime.datetime.strptime(val, "%d.%m.%Y")


class UBSCSVParser(BaseSwissParser):
    """
    Parser for UBS CSV Statements
    """

    _ftype = 'ubs_csvparser'

    def __init__(self, data_file):
        """Constructor
        Splitting data_file in lines and create a dict from the csv file
        """

        super(UBSCSVParser, self).__init__(data_file)
        rows = []
        self.lines = self.data_file.splitlines()
        reader = csv.DictReader(self.lines[:-3], delimiter=';')

        for row in reader:
            rows.append(
                dict([(key.decode('iso-8859-15'), value.decode('iso-8859-15'))
                      for key, value in row.iteritems()]))

        self.datas = rows

    def file_is_known(self):
        """Predicate the tells if the parser can parse the data file

        :return: True if file is supported
        :rtype: bool
        """
        return len(self.datas) > 1 and ('IBAN' in self.datas[1])

    def _parse_currency_code(self):
        """Parse file currency ISO code

        :return: the currency ISO code of the file eg: CHF
        :rtype: string
        """

        return 'CHF'

    def _parse_statement_balance(self):
        """Parse file start and end balance

        :return: Tuple of the file start and end balance
        :rtype: float
        """

        solde_line = self.lines[-1].split(";")
        balance_end = float_or_zero(solde_line[0])
        balance_start = float_or_zero(solde_line[1])
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
        for line in self.datas:
            descriptions = [
                line.get("Description 1", '/'), line.get("Description 2", ''),
                line.get("Description 3", '')]
            label = ' '.join(filter(None, descriptions))

            debit = u"Débit"
            credit = u"Crédit"
            amount = - float_or_zero(line[debit]) or \
                float_or_zero(line[credit]) or 0.0
            res = {
                'name': label,
                'date': format_date(line.get("Date de comptabilisation")),
                'amount': amount,
                'ref': '/',
                'note': label,
                'unique_import_id': str(uuid.uuid4())
            }

            transactions.append(res)

        return transactions

    def _parse_statement_date(self):
        """Parse file statement date
        :return: A date usable by Odoo in write or create dict
        """

        return fields.Date.today()

    def _parse(self):
        """
        Launch the parsing through the csv file.
        """

        self.currency_code = self._parse_currency_code()
        balance_start, balance_end = self._parse_statement_balance()
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
