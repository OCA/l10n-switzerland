# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Emanuel Cino
#    Copyright 2014 Compassion CH
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
from datetime import date
import time
from openerp.osv.osv import except_osv
from account_statement_base_import.parser.parser \
    import BankStatementImportParser
from openerp.tools.translate import _

reject_reason = {
    '01': _("Insufficient cover funds."),
    '02': _("Debtor protestation."),
    '03': _("Debtor’s account number and address do not match."),
    '04': _("Postal account closed."),
    '05': _("Postal account blocked/frozen."),
    '06': _("Postal account holder deceased."),
    '07': _("Postal account number non-existent.")
}


class G11FileParser(BankStatementImportParser):
    """
    Parser for a .v11 file in the BVR DD type 2 format.
    """

    def __init__(self, parser_name, ftype='g11', **kwargs):
        super(G11FileParser, self).__init__(parser_name, **kwargs)

        if ftype != 'g11':
            raise except_osv(_('User Error'),
                             _('Invalid file type %s. Please use g11') %
                             ftype)

        # Store the lines of the file in an array
        self.lines = None

        # Store the amount of failed transactions
        self.amount_fail = 0.0

        # Store the number of transactions.
        self.transactions = 0

    @classmethod
    def parser_for(cls, parser_name):
        return parser_name == 'g11_fileparser'

    def _custom_format(self, *args, **kwargs):
        # Nothing to do
        return True

    def _pre(self, *args, **kwargs):
        """
        Check the last total record.
        """
        self.lines = self.filebuffer.splitlines()
        self.balance_start = 0.0
        self.balance_end = 0.0
        if self.lines[-1][0:3] != '097':
            raise except_osv(_("Wrong formatting"),
                             _("The total record could not be read. \
                             Please provide a valid g11 file."))
        return True

    def _parse(self, *args, **kwargs):
        """
        Implement a method in your parser to save the result of parsing
        self.filebuffer in self.result_row_list instance property.
        """
        res = []
        for line in self.lines:
            if line[0:3] == '097':
                self._parse_total_line(line)
            else:
                ref = line[15:42]
                currency = line[42:45]
                amount = float(line[45:57]) / 100
                transaction_date = time.strftime(
                    '%Y-%m-%d', time.strptime(line[108:116], '%Y%m%d'))
                # commission = float(line[141:147]) / 100
                label = ''

                if line[0:3] == '084':
                    # Fail / Debit record
                    reject_code = line[128:130]
                    if reject_code == '02':
                        # Debit record
                        amount *= -1
                        label = reject_reason[reject_code]
                    else:
                        # Failed transactions. Get the error reason and
                        # put it on the OBI field.
                        label = reject_reason[
                            reject_code] + '\n' + _(
                                "Amount to debit was %s %f") % (
                                    currency, amount)
                        amount = 0.0

                # Add information to OBI if the transaction is a test.
                if line[5] == '3':
                    label = _("-- Test transaction --") + '\n' + label

                res.append({
                    'ref': ref,
                    'currency': currency,
                    'amount': amount,
                    'date': transaction_date,
                    'label': label,
                })

        self.result_row_list = res
        return True

    def _parse_total_line(self, total_line):
        self.balance_end += (
            float(total_line[45:57]) / 100) - (
                float(total_line[101:113]) / 100)
        # self.commission = float(total_line[131:142]) / 100  # not used
        # self.amount_fail = float(total_line[77:89]) / 100  # not used
        self.transactions += int(
            total_line[57:69]) + int(
                total_line[89:101]) + int(
                    total_line[113:125])
        # Store the currency
        self.currency = total_line[128:131]

    def _validate(self, *args, **kwargs):
        """
        Test we have the correct number of transactions.
        """
        if len(self.result_row_list) != self.transactions:
            raise except_osv(_("Invalid number of transactions"),
                             _("The number of transactions read is not \
                             the same as the one provided in the \
                             total record."))

        return True

    def _post(self, *args, **kwargs):
        """
        Nothing to process here.
        """
        return True

    def get_st_line_vals(self, line, *args, **kwargs):
        """
            Returns the values for creating the statement line.

            :param:  line: a dict of vals that represent a line of
                           result_row_list
            :return: dict of values to give to the create method of
                     statement line,
        """
        res = {
            'name': line.get("label", "/"),
            'date': line.get('date', date.today()),
            'amount': line.get('amount', 0.0),
            'ref': line.get('ref', '/'),
            'label': line.get("label"),
        }

        return res
