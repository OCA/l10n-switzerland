# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2015 brain-tec AG (http://www.braintec-group.com)
#    All Right Reserved
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

import time
from lxml import etree

from openerp import models, fields, api, _


class PaymentOrderCreate(models.TransientModel):
    """
    Create a payment object with lines corresponding to the account move line
    to pay according to the date and the mode provided by the user.
    Hypothesis:
    - Small number of non-reconciled move line, payment mode and
    bank account type,
    - Big number of partner and bank account.

    If a type is given, unsuitable account Entry lines are ignored.
    """

    _name = 'payment.order.create'
    _description = 'payment.order.create'

    duedate = fields.Date('Due Date', required=True,
                          default=lambda *a: time.strftime('%Y-%m-%d'))

    entries = fields.Many2many('account.move.line', 'line_pay_rel', 'pay_id',
                               'line_id')

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        res = super(PaymentOrderCreate, self).\
            fields_view_get(view_id=view_id, view_type=view_type,
                            toolbar=toolbar, submenu=False)

        context = dict(self._context or {})
        if context and 'line_ids' in context:
            doc = etree.XML(res['arch'])
            nodes = doc.xpath("//field[@name='entries']")
            for node in nodes:
                node.set('domain', '[("id", "in", ' +
                         str(context['line_ids']) + ')]')
            res['arch'] = etree.tostring(doc)
        return res

    @api.one
    def create_payment(self):
        order_obj = self.env['payment.register']
        line_obj = self.env['account.move.line']
        reg_line_obj = self.env['payment.register.line']

        context = dict(self._context or {})
        line_ids = [entry.id for entry in self.entries]
        if not line_ids:
            return {'type': 'ir.actions.act_window_close'}

        payment = order_obj.browse(context['active_id'])
        line2bank = line_obj.line2bank(line_ids)

        # # Finally populate the current payment with new lines:
        for line in line_obj.browse(line_ids):
            if payment.date_prefered == "now":
                # no payment date => immediate payment
                date_to_pay = False
            elif payment.date_prefered == 'due':
                date_to_pay = line.date_maturity
            elif payment.date_prefered == 'fixed':
                date_to_pay = payment.date_scheduled
            reg_line_obj.\
                create({'name': line.name,
                        'move_line_id': line.id,
                        'amount_currency': line.credit,
                        'bank_id': line2bank.get(line.id),
                        'order_id': payment.id,
                        'partner_id': (line.partner_id and
                                       line.partner_id.id or False),
                        'communication': line.ref or '/',
                        'state': (line.invoice_id and
                                  line.invoice_id.reference_type != 'none' and
                                  'structured' or 'normal'),
                        'date': date_to_pay,
                        'currency_id': ((line.company_id and
                                         line.company_id.currency_id.id) or
                                        (line.invoice_id and
                                        line.invoice_id.currency_id.id)),
                        })
        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def search_entries(self):
        line_obj = self.env['account.move.line']
        mod_obj = self.env['ir.model.data']

        search_due_date = self.duedate

        # Search for move line to pay:
        domain = [('reconciled', '=', False),
                  ('account_id.internal_type', '=', 'payable'),
                  ('credit', '>', 0), ('account_id.reconcile', '=', True)]

        domain = domain + ['|', ('date_maturity', '<=', search_due_date),
                           ('date_maturity', '=', False)]

        line_ids = line_obj.search(domain)

        ctx = self.env.context.copy()
        ctx.update({'line_ids': line_ids.ids})

        model_data_ids = mod_obj.\
            search([('model', '=', 'ir.ui.view'),
                    ('name', '=', 'view_payment_order_create_lines')])

        resource_id = mod_obj.browse(model_data_ids.ids)[0]['res_id']
        return {'name': _('Entry Lines'),
                'context': ctx,
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'payment.order.create',
                # 'view_id': resource_id,
                'views': [(resource_id, 'form')],
                'type': 'ir.actions.act_window',
                'target': 'new',
                'domain': [('entries', 'in', line_ids.ids)],
                }
