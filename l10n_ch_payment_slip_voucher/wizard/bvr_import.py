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
import time
from openerp.tools.translate import _


class BvrImporterWizard(models.TransientModel):

    def _get_default_currency_id(self):
        return self.env.user.company_id.currency_id.id

    _name = 'v11.import.wizard.voucher'
    v11file = fields.Binary('V11 File')
    total_cost = fields.Float('Total cost of V11')
    total_amount = fields.Float('Total amount of V11')
    journal_id = fields.Many2one(
        'account.journal', "Journal", required=True)
    currency_id = fields.Many2one(
        'res.currency', "Currency", required=True,
        default=_get_default_currency_id)
    validate_vouchers = fields.Boolean(
        "Validate vouchers",
        help="Activate this to automatically validate every created voucher")

    def _build_voucher_header(self, partner, record):
        date = record['date'] or fields.Date.today()
        voucher_vals = {
            'type': 'receipt',
            'name': record['reference'],
            'partner_id': partner.id,
            'journal_id': self.journal_id.id,
            'account_id': self.journal_id.default_credit_account_id.id,
            'company_id': self.journal_id.company_id.id,
            'currency_id': self.currency_id.id,
            'date': date,
            'amount': abs(record['amount']),
            }
        return voucher_vals

    def _build_voucher_line(self, partner, record, voucher_id):
        voucher_obj = self.env['account.voucher']
        date = fields.Date.today()
        result = voucher_obj.onchange_partner_id(partner.id,
                                                 self.journal_id.id,
                                                 abs(record['amount']),
                                                 self.currency_id.id,
                                                 'receipt',
                                                 date)
        voucher_line_dict = False
        move_line_obj = self.env['account.move.line']
        if result['value']['line_cr_ids']:
            for line_dict in result['value']['line_cr_ids']:
                move_line = move_line_obj.browse(line_dict['move_line_id'])
                if move_line.transaction_ref == record['reference']:
                    voucher_line_dict = line_dict
                    break
        if voucher_line_dict:
            voucher_line_dict.update({'voucher_id': voucher_id})
        return voucher_line_dict

    def get_partner_from_ref(self, reference):
        move_line_obj = self.env['account.move.line']
        line = move_line_obj.search(
            [('transaction_ref', '=', reference),
             ('reconcile_id', '=', False),
             ('account_id.type', 'in', ['receivable', 'payable']),
             ('journal_id.type', '=', 'sale')],
            order='date desc',
        )
        if not line:
            raise exceptions.Warning(
                "Can't find credit line for reference %s" % reference)
        if len(line) > 1:
            raise exceptions.Warning(
                "Too many credit lines for reference %s" % reference)
        if not line.partner_id:
            raise exceptions.Warning(
                "Can't find a partner for reference %s" % reference)
        return line.partner_id

    def _import_v11(self):
        """Import v11 file and transfor it into vouchers

        :returns: action dict
        :rtype: dict
        """
        attachment_obj = self.env['ir.attachment']
        v11_wizard = self.env['v11.import.wizard']
        voucher_obj = self.env['account.voucher']
        voucher_line_obj = self.env['account.voucher.line']
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
        std_importer = v11_wizard.create({
            'v11file': self.v11file,
            'total_cost': self.total_cost,
            'total_amount': self.total_amount,
            })
        records = std_importer._parse_lines(lines)
        voucher_ids = []
        for record in records:
            partner = self.get_partner_from_ref(record['reference'])
            voucher = voucher_obj.create(
                self._build_voucher_header(partner, record))
            voucher_line_obj.create(
                self._build_voucher_line(partner, record, voucher.id))
            voucher_ids.append(voucher.id)
        for voucher_id in voucher_ids:
            attachment_obj.create(
                {
                    'name': 'V11 %s' % time.strftime(
                        "%Y-%m-%d_%H:%M:%S", time.gmtime()
                    ),
                    'datas': self.v11file,
                    'datas_fname': 'BVR %s.txt' % time.strftime(
                        "%Y-%m-%d_%H:%M:%S", time.gmtime()
                    ),
                    'res_model': 'account.voucher',
                    'res_id': voucher_id,
                },
            )
            if self.validate_vouchers:
                voucher = voucher_obj.browse(voucher_id)
                voucher.signal_workflow('proforma_voucher')

        action_res = self.env['ir.actions.act_window'].for_xml_id(
            'account_voucher', 'action_vendor_receipt')
        action_res['domain'] = [('id', 'in', voucher_ids)]
        return action_res

    @api.multi
    def import_v11(self):
        """Import v11 file and transfor it into voucher lines

        :returns: action dict
        :rtype: dict
        """
        return self._import_v11()
