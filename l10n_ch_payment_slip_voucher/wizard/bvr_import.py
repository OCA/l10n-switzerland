# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2014 Agile Business Group <http://www.agilebg.com>
#    Author: Lorenzo Battistini <lorenzo.battistini@agilebg.com>
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

from openerp import models, fields, exceptions, api
import base64


class BvrImporterWizard(models.TransientModel):
    _name = 'v11.import.wizard.voucher'
    v11file = fields.Binary('V11 File')
    total_cost = fields.Float('Total cost of V11')
    total_amount = fields.Float('Total amount of V11')
    journal_id = fields.Many2one('account.journal', "Journal", required=True)

    @api.model
    def _prepare_line_vals(self, statement, record):
        """Compute voucher values to be used by `models.Model.create'
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
        line_ids = move_line_obj.search(
            [('transaction_ref', '=', reference),
             ('reconcile_id', '=', False),
             ('account_id.type', 'in', ['receivable', 'payable']),
             ('journal_id.type', '=', 'sale')],
            order='date desc',
        )
        if line_ids:
            # transaction_ref is propagated on all lines
            line = move_line_obj.browse(line_ids[0])
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
        attachment_obj = self.env['ir.attachment']
        v11_wizard = self.env['v11.import.wizard']
        v11file = self.v11file
        if not v11file:
            raise exceptions.Warning(
                _('Please select a file first!')
            )
        try:
            lines = base64.decodestring(v11file).split("\r\n")
        except ValueError as decode_err:
            raise exceptions.Warning(
                _('V11 file can not be decoded, '
                  'it contains invalid caracter %s'),
                repr(decode_err)
            )
        records = v11_wizard._parse_lines(lines)

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
        """Import v11 file and transfor it into voucher lines

        :returns: action dict
        :rtype: dict
        """
        return self._import_v11()
