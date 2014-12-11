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
    currency_id = fields.Many2one('res.currency', "Currency", required=True) # TODO default

    def _build_voucher_header(self, partner_id, record):
        voucher_obj = self.env['account.voucher']
        date = record['date'] or time.strftime('%Y-%m-%d')
        voucher_vals {
            'type': 'receipt',
            'name': record['reference'],
            'partner_id': partner_id,
            'journal_id': self.journal_id.id,
            'account_id': self.journal_id.default_credit_account_id.id,
            'company_id': self.journal_id.company_id.id,
            'currency_id': self.currency_id.id,
            'date': date,
            'amount': abs(record['amount']),
            }

    def _build_voucher_lines(self, partner_id, record, voucher_id):
        voucher_obj = self.env['account.voucher']
        result = voucher_obj.onchange_partner_id(self.env.cr, self.env.uid, [],
                                                 partner_id,
                                                 self.journal_id.id,
                                                 abs(record['amount']),
                                                 self.currency_id.id,
                                                 'receipt',
                                                 date,
                                                 context=self.env.context)
        voucher_line_dict = False
        if result['value']['line_cr_ids']:
            for line_dict in result['value']['line_cr_ids']:
                move_line = move_line_obj.browse(
                    cursor, uid, line_dict['move_line_id'], context)
                if move_id == move_line.move_id.id:
                    voucher_line_dict = line_dict
        if voucher_line_dict:
            voucher_line_dict.update({'voucher_id': voucher_id})
            voucher_line_obj.create(
                cursor, uid, voucher_line_dict, context=context)

    def _search_move_lines(self, record):
        move_line_obj = self.env['account.move.line']
        reference = record['reference']
        line_ids = move_line_obj.search(
            [('transaction_ref', '=', reference),
             ('reconcile_id', '=', False),
             ('account_id.type', 'in', ['receivable', 'payable']),
             ('journal_id.type', '=', 'sale')],
            order='date desc',
        )
        return line_ids

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
        move_lines = []
        for record in records:
            move_lines.append(self._search_move_lines(record))
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
