# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi. Copyright Camptocamp SA
#    Financial contributors: Hasa SA, Open Net SA,
#                            Prisme Solutions Informatique SA, Quod SA
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
import base64
import time
import re

from openerp.tools.translate import _
from openerp import models, fields, exceptions, api
from openerp.tools.misc import mod10r

REF = re.compile(r'[^0-9]')


class BvrImporterWizard(models.TransientModel):

    _name = 'v11.import.wizard'
    _total_line_codes = ('999', '995')

    v11file = fields.Binary('V11 File')
    total_cost = fields.Float('Total cost of V11')
    total_amount = fields.Float('Total amount of V11')

    @api.model
    def _get_line_amount(self, line, sum_amount=True):
        """Returns the V11 line amount value
        :param line: raw v11 line
        :type line: str

        :param sum_amount: if True total_amount will be sum with current amount
        :type sum_amount: bool

        :return: current line amount
        :rtype: float
        """
        if line[0:3] in self._total_line_codes:
            amount = float(line[39:51]) / 100.0
        else:
            amount = float(line[39:49]) / 100.0
        if line[2] == '5':
            amount *= -1
        if sum_amount:
            self.total_amount += amount
        return amount

    def _validate_total_amount(self, amount):
        """Ensure total amount match given amount
        :param: amount to validate
        :type amount: float
        """
        if round(amount - self.total_amount, 2) >= 0.01:
            raise exceptions.Warning(
                _('Total amount differ from the computed amount')
            )

    @api.model
    def _get_line_cost(self, line, sum_cost=True):
        """Returns the V11 line cost value
        :param line: raw v11 line
        :type line: str

        :param sum_cost: if True cost_amount will be sum with current amount
        :type sum_cost: bool

        :return: current line cost
        :rtype: float
        """
        if line[0:3] in self._total_line_codes:
            cost = float(line[69:78]) / 100.0
        else:
            cost = float(line[96:100]) / 100.0
        if line[2] == '5':
            cost *= -1
        if sum_cost:
            self.total_cost += cost
        return cost

    def _validate_total_cost(self, cost):
        """Ensure total cost match given cost
        :param: cost to validate
        :type cost: float
        """
        if round(cost - self.total_cost, 2) >= 0.01:
            raise exceptions.Warning(
                _('Total cost differ from the computed amount')
            )

    @api.model
    def _create_record(self, line):
        """Create a v11 record dict
        :param line: raw v11 line
        :type line: str

        :return: current line dict representation
        :rtype: dict

        """
        amount = self._get_line_amount(line)
        cost = self._get_line_cost(line)
        record = {
            'reference': line[12:39],
            'amount': amount,
            'date': time.strftime(
                '%Y-%m-%d',
                time.strptime(line[65:71], '%y%m%d')
            ),
            'cost': cost,
        }

        if record['reference'] != mod10r(record['reference'][:-1]):
            raise exceptions.Warning(
                _('Recursive mod10 is invalid for reference: %s') %
                record['reference']
            )
        return record

    @api.model
    def _parse_lines(self, inlines):
        """Parses raw v11 line and populate records list with dict

        :param inlines: string buffer of the V11 file
        :type inlines: str

        :return: list of dict representing a v11 entry
        :rtype: list of dict
        """
        records = []
        find_total = False
        for lines in inlines:
            if not lines:  # manage new line at end of file
                continue
            (line, lines) = (lines[:128], lines[128:])
            record = {}
            # If line is a validation line
            if line[0:3] in self._total_line_codes:
                if find_total:
                    raise exceptions.Warning(
                        _('Too many total record found!')
                    )
                find_total = True
                if lines:
                    raise exceptions.Warning(
                        _('Record found after total record')
                    )
                if int(line[51:63]) != len(records):
                    raise exceptions.Warning(
                        _('Number of records differ from the computed one')
                    )
                # Validaton of amount and costs
                amount = self._get_line_amount(line, sum_amount=False)
                cost = self._get_line_cost(line, sum_cost=False)
                self._validate_total_amount(amount)
                self._validate_total_cost(cost)
            else:
                record = self._create_record(line)
                records.append(record)
        return records

    @api.model
    def _prepare_line_vals(self, statement, record):
        """Compute bank statement values to be used by `models.Model.create'
        :param statement: current statement record
        :type statement: :py:class:`openerp.models.Models` record

        :param record: dict reprenting parsed V11 line
        :type record: dict

        :returns: values
        :rtype: dict
        """
        # Remove the 11 first char because it can be adherent number
        # TODO check if 11 is the right number
        move_line_obj = self.env['account.move.line']
        reference = record['reference']
        values = {'name': reference or '/',
                  'date': record['date'],
                  'amount': record['amount'],
                  'ref': '/',
                  'type': (record['amount'] >= 0 and 'customer') or 'supplier',
                  'statement_id': statement.id,
                  }
        line = move_line_obj.search(
            [('transaction_ref', '=', reference),
             ('reconcile_id', '=', False),
             ('account_id.type', 'in', ['receivable', 'payable']),
             ('journal_id.type', '=', 'sale')],
            order='date desc',
        )
        if len(line) > 1:
            raise exceptions.Warning(
                _("Too many receivable/payable lines for reference %s")
                % reference)
        if line:
            # transaction_ref is propagated on all lines
            partner_id = line.partner_id.id
            num = line.invoice.number if line.invoice else False
            values['ref'] = _('Inv. no %s') % num if num else values['name']
            values['partner_id'] = partner_id
        return values

    def _import_v11(self):
        """Import v11 file and transfor it into statement lines

        :returns: action dict
        :rtype: dict
        """
        statement_line_obj = self.env['account.bank.statement.line']
        attachment_obj = self.env['ir.attachment']
        statement_obj = self.env['account.bank.statement']
        v11file = self.v11file
        if not v11file:
            raise exceptions.Warning(
                _('Please select a file first!')
            )
        statement_id = self.env.context.get('active_id')
        if not statement_id:
            raise ValueError('The id of current satement is not in statement')
        try:
            lines = base64.decodestring(v11file).split("\r\n")
        except ValueError as decode_err:
            raise exceptions.Warning(
                _('V11 file can not be decoded, '
                  'it contains invalid caracter %s'),
                repr(decode_err)
            )
        records = self._parse_lines(lines)

        statement = statement_obj.browse(statement_id)
        for record in records:
            values = self._prepare_line_vals(statement,
                                             record)
            statement_line_obj.create(values)
        attachment_obj.create(
            {
                'name': 'V11 %s' % time.strftime(
                    "%Y-%m-%d_%H:%M:%S", time.gmtime()
                ),
                'datas': self.v11file,
                'datas_fname': 'BVR %s.txt' % time.strftime(
                    "%Y-%m-%d_%H:%M:%S", time.gmtime()
                ),
                'res_model': 'account.bank.statement',
                'res_id': statement.id,
            },
        )

        return {}

    @api.multi
    def import_v11(self):
        """Import v11 file and transfor it into statement lines

        :returns: action dict
        :rtype: dict
        """
        return self._import_v11()
