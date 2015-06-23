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
import re
import time
from datetime import date
from openerp.osv.osv import except_osv
from account_statement_base_import.parser.parser \
    import BankStatementImportParser
from openerp.tools.translate import _


def is_total_record_type4(test):
    return re.compile("^9[89][12]$").match(test)


class V11FileParser(BankStatementImportParser):
    """
    A v11 file parser.
    """

    def __init__(self, parser_name, ftype='v11', **kwargs):
        super(V11FileParser, self).__init__(parser_name, **kwargs)

        if ftype.lower() not in ('v11', 'esr', 'bvr'):
            raise except_osv(_('User Error'),
                             _('Invalid file type %s. Please use v11, \
                             esr or bvr') % ftype)

        # Store the record_type of the ESR file (can be of type 3 or 4).
        self.record_type = None

        # Store the lines of the file in an array
        self.lines = None

    @classmethod
    def parser_for(cls, parser_name):
        return parser_name == 'esr_fileparser'

    def _custom_format(self, *args, **kwargs):
        # Nothing to do
        return True

    def _pre(self, *args, **kwargs):
        """
        Check which kind of record type is the file, by looking at
        the total line.
        """
        self.lines = self.filebuffer.splitlines()
        total_line = self.lines[-1]
        total_code = total_line[0:3]
        if total_code in ('999', '995'):
            self.record_type = 3
            self.balance_start = 0
            self.balance_end = (float(total_line[39:51]) / 100)
            self.number_transaction = int(total_line[51:63])
        elif is_total_record_type4(total_code):
            self.record_type = 4
        return True

    def _parse(self, *args, **kwargs):
        res = []
        if self.record_type == 3:
            res = self._parse_type3()
        elif self.record_type == 4:
            res = self._parse_type4()
        else:
            raise except_osv(_('User Error'),
                             _('Invalid file. Please use a valid v11, \
                             esr or bvr file.'))

        self.result_row_list = res
        return True

    def _parse_type3(self):
        """
        Parse ESR record of type 3
        """
        res = []
        for line in self.lines[:-1]:
            if line[0:3] in ('999', '995'):
                # Total line : addition the amount to the balance_end
                self.balance_end += (float(line[39:51]) / 100)
                self.number_transaction += int(line[51:63])
            else:
                reference = line[12:39]
                amount = float(line[39:49]) / 100
                format_date = time.strftime(
                    '%Y-%m-%d', time.strptime(line[71:77], '%y%m%d'))
                cost = float(line[96:100]) / 100  # not used

                if line[2] == '5':
                    amount *= -1
                    cost *= -1

                res.append({
                    'ref': reference,
                    'amount': amount,
                    'date': format_date,
                })

        return res

    def _parse_type4(self):
        """
        Parse ESR record of type 4. This method is not implemented. Feel free
        to inherit from this class in your module in order to implement it.
        """
        return NotImplementedError

    def _validate(self, *args, **kwargs):
        """
        We check our results against the total line for record of type 3.
        Inherit this method to add validation for record type 4.
        """
        if self.record_type == 3:
            if not len(self.result_row_list) == self.number_transaction:
                raise except_osv(_('Invalid data'),
                                 _('The number of read transactions doesn\'t match the \
                                 total records in file'))

        return True

    def _post(self, *args, **kwargs):
        """
        Nothing to do here.
        """
        return True

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
            'name': '/',
            'date': line.get('date', date.today()),
            'amount': line.get('amount', 0.0),
            'ref': line.get('ref', '/'),
        }

        return res
