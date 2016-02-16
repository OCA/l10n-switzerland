# b-*- encoding: utf-8 -*-
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

from openerp import models, fields, api, _


class payment_line(models.Model):
    _name = 'payment.register.line'
    _description = 'Payment Line'

    def translate(self, orig):
        return {"due_date": "date_maturity",
                "reference": "ref"}.get(orig, orig)

    def _info_owner(self, name=None):
        result = {}
        for line in self:
            owner = line.order_id.mode.bank_id.partner_id
            result[line.id] = self._get_info_partner(owner)
        return result

    def _get_info_partner(self, partner_record):
        if not partner_record:
            return False
        st = partner_record.street or ''
        st1 = partner_record.street2 or ''
        zip = partner_record.zip or ''
        city = partner_record.city or ''
        zip_city = zip + ' ' + city
        cntry = partner_record.country_id and partner_record.country_id.name or ''
        return partner_record.name + "\n" + st + " " + st1 + "\n" + zip_city + "\n" + cntry

    def _info_partner(self, name=None):
        result = {}
        for line in self:
            result[line.id] = False
            if not line.partner_id:
                break
            result[line.id] = self._get_info_partner(line.partner_id)
        return result

    @api.one
    def _compute_amount(self):
        amount = self.amount_currency
        if self.company_currency:
            self.with_context(date=self.order_id.date_done or time.strftime('%Y-%m-%d'))
            amount = self.company_currency.compute(self.amount_currency, self.currency_id)
        return amount

    @api.one
    def _get_currency(self):
        user_obj = self.env['res.users']
        currency_obj = self.env['res.currency']
        user = user_obj.browse(self._uid)

        if user.company_id:
            return user.company_id.currency_id.id
        else:
            return currency_obj.search([('rate', '=', 1.0)])[0]

    @api.one
    def _get_date(self):
        payment_order_obj = self.env['payment.register']
        date = False
        order_id = self.env.context.get('order_id')
        if order_id:
            order = payment_order_obj.browse(order_id)
            if order.date_prefered == 'fixed':
                date = order.date_scheduled
            else:
                date = time.strftime('%Y-%m-%d')
        return date

    name = fields.Char('Your Reference', required=True)
    communication = fields.Char('Communication', required=True,
                                help="Used as the message between ordering "
                                "customer and current company. Depicts"
                                "'What do you want to say to the recipient about this order ?'")

    communication2 = fields.Char('Communication 2',
                                 help='The successor message of Communication.')

    move_line_id = fields.Many2one('account.move.line', 'Entry line',
                                       domain=[('reconciled', '=', False), ('account_id.internal_type', '=', 'payable')],
                                       help='This Entry Line will be referred for the information of the ordering customer.')

    amount_currency = fields.Float('Amount in Partner Currency', digits=(16, 2),
                                   required=True,
                                   help='Payment amount in the partner currency')

    currency_id = fields.Many2one('res.currency', 'Partner Currency',
                                  required=True, default=_get_currency)

    company_currency = fields.Many2one('res.currency', 'Company Currency',
                                       readonly=True, default=_get_currency)

    bank_id = fields.Many2one('res.partner.bank', 'Destination Bank Account')

    order_id = fields.Many2one('payment.register', 'Order', required=True,
                               ondelete='cascade', select=True)

    partner_id = fields.Many2one('res.partner', string="Partner", required=True,
                                 help='The Ordering Customer')

    amount = fields.Float(compute="_compute_amount", string='Amount in Company Currency',
                          help='Payment amount in the company currency')

    ml_date_created = fields.Datetime(related="move_line_id.create_date",
                                      string="Effective Date",
                                      help="Invoice Effective Date")

    ml_maturity_date = fields.Date(related="move_line_id.date_maturity",
                                   string='Due Date')

    ml_inv_ref = fields.Many2one('account.invoice',
                                 related="move_line_id.invoice_id",
                                  string='Invoice Ref.')

    info_owner = fields.Text(compute="_info_owner", string="Owner Account",
                             help='Address of the Main Partner')

    info_partner = fields.Text(compute="_info_partner",
                               string="Destination Account",
                                help='Address of the Ordering Customer.')

    date = fields.Date('Payment Date', help="If no payment date is specified, the bank will treat this payment line directly",
                        default=_get_date)

    state = fields.Selection([('normal', 'Free'), ('structured', 'Structured')],
                             'Communication Type', required=True,
                             default='normal')

    bank_statement_line_id = fields.Many2one('account.bank.statement.line', 'Bank statement line')

    company_id = fields.Many2one('res.company', related='order_id.company_id',
                                 string='Company', store=True, readonly=True)

    _sql_constraints = [
        ('name_uniq', 'UNIQUE(name)', 'The payment line name must be unique!'),
    ]

# IMPLEMENT IF NECESSARY
#     @api.multi
#     @api.onchange('move_line_id')
#     def onchange_move_line(self, cr, uid, ids, move_line_id, payment_type, date_prefered, date_scheduled, currency_id=False, company_currency=False, context=None):
#         data = {}
#         move_line_obj = self.pool.get('account.move.line')
#
#         data['amount_currency'] = data['communication'] = data['partner_id'] = data['bank_id'] = data['amount'] = False
#
#         if move_line_id:
#             line = move_line_obj.browse(cr, uid, move_line_id, context=context)
#             data['amount_currency'] = line.amount_residual_currency
#
#             res = self.onchange_amount(cr, uid, ids, data['amount_currency'], currency_id,
#                                        company_currency, context)
#             if res:
#                 data['amount'] = res['value']['amount']
#             data['partner_id'] = line.partner_id.id
#             temp = line.currency_id and line.currency_id.id or False
#             if not temp:
#                 if line.invoice:
#                     data['currency_id'] = line.invoice.currency_id.id
#             else:
#                 data['currency_id'] = temp
#
#             # calling onchange of partner and updating data dictionary
#             temp_dict = self.onchange_partner(cr, uid, ids, line.partner_id.id, payment_type)
#             data.update(temp_dict['value'])
#
#             data['communication'] = line.ref
#
#             if date_prefered == 'now':
#                 #no payment date => immediate payment
#                 data['date'] = False
#             elif date_prefered == 'due':
#                 data['date'] = line.date_maturity
#             elif date_prefered == 'fixed':
#                 data['date'] = date_scheduled
#         return {'value': data}

#     def onchange_amount(self, cr, uid, ids, amount, currency_id, cmpny_currency, context=None):
#         if (not amount) or (not cmpny_currency):
#             return {'value': {'amount': False}}
#         res = {}
#         currency_obj = self.pool.get('res.currency')
#         company_amount = currency_obj.compute(cr, uid, currency_id, cmpny_currency, amount)
#         res['amount'] = company_amount
#         return {'value': res}
#
#     def onchange_partner(self, cr, uid, ids, partner_id, payment_type, context=None):
#         data = {}
#         partner_obj = self.pool.get('res.partner')
#         payment_mode_obj = self.pool.get('payment.mode')
#         data['info_partner'] = data['bank_id'] = False
#
#         if partner_id:
#             part_obj = partner_obj.browse(cr, uid, partner_id, context=context)
#             partner = part_obj.name or ''
#             data['info_partner'] = self._get_info_partner(cr, uid, part_obj, context=context)
#
#             if part_obj.bank_ids and payment_type:
#                 bank_type = payment_mode_obj.suitable_bank_types(cr, uid, payment_type, context=context)
#                 for bank in part_obj.bank_ids:
#                     if bank.state in bank_type:
#                         data['bank_id'] = bank.id
#                         break
#         return {'value': data}

#     def fields_get(self, fields=None):
#         res = super(payment_line, self).fields_get(fields)
#         if 'communication2' in res:
#             res['communication2'].setdefault('states', {})
#             res['communication2']['states']['structured'] = [('readonly', True)]
#             res['communication2']['states']['normal'] = [('readonly', False)]
#         return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
