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
from openerp import models, fields, api


class PaymentRegister(models.Model):
    _name = 'payment.register'
    _description = 'Payment Register'
    _rec_name = 'reference'
    _order = 'id desc'

    @api.multi
    @api.depends('line_ids.amount')
    def _compute_total(self):
        for payment_register in self:
            total = 0
            for line in payment_register.line_ids:
                total += line.amount
            payment_register.total = total

    date_scheduled = fields.Date('Scheduled Date',
                                 states={'done': [('readonly', True)]},
                                 help='Select a date if you have chosen '
                                 'Preferred Date to be fixed.')

    reference = fields.Char('Reference', required=1,
                            states={'done': [('readonly', True)]},
                            default=lambda self:
                            self.env['ir.sequence'].get('payment.register'),
                            copy=False)

    mode = fields.Many2one('payment.mode', 'Payment Mode', select=True,
                           required=1, states={'done': [('readonly', True)]},
                           help='Select the Payment Mode to be applied.')

    state = fields.Selection([('draft', 'Draft'),
                              ('cancel', 'Cancelled'),
                              ('open', 'Confirmed'),
                              ('done', 'Done')], 'Status', select=True,
                             copy=False, default='draft',
                             help='When an order is placed the status is '
                             '\'Draft\'.\n Once the bank is confirmed the '
                             'status is set to \'Confirmed\'.\n'
                             'Then the order is paid the status is \'Done\'.')

    line_ids = fields.One2many('payment.register.line', 'order_id',
                               'Payment lines',
                               states={'done': [('readonly', True)]})

    total = fields.Float(compute='_compute_total', string="Total")

    user_id = fields.Many2one('res.users', 'Responsible', required=True,
                              states={'done': [('readonly', True)]},
                              default=lambda self: self.env.uid)

    date_prefered = fields.\
        Selection([('now', 'Directly'), ('due', 'Due date'),
                   ('fixed', 'Fixed date')
                   ], "Preferred Date", change_default=True, default='due',
                  required=True, states={'done': [('readonly', True)]},
                  help="Choose an option for the Payment Order:'Fixed'"
                       "stands for a date specified by you.'Directly' stands "
                       "for the direct execution. 'Due date' stands for the "
                       "scheduled date of execution.")

    date_created = fields.Date('Creation Date', readonly=True,
                               default=lambda *a: time.strftime('%Y-%m-%d'))

    date_done = fields.Date('Execution Date', readonly=True)

    company_id = fields.Many2one('res.company', related='mode.company_id',
                                 string='Company', store=True, readonly=True)

    entries_test = fields.Many2many('account.move.line', 'test_line_pay_rel',
                                    'pay_id', 'line_id')

    @api.one
    def set_to_draft(self):
        self.write({'state': 'draft'})
#         self.create_workflow()
        return True

    @api.one
    def set_to_confirmed(self):
        self.write({'state': 'open'})
#         self.create_workflow()
        return True

    @api.one
    def set_done(self):
        self.write({'date_done': time.strftime('%Y-%m-%d'), 'state': 'done'})
#         self.signal_workflow('done')
        return True

    @api.one
    def write(self, vals):

        payment_line_obj = self.env['payment.register.line']
        payment_line_ids = []

        if ((vals.get('date_prefered', False) == 'fixed' and not
             vals.get('date_scheduled', False)) or
                vals.get('date_scheduled', False)):
            for order in self:
                for line in order.line_ids:
                    payment_line_ids.append(line.id)
            payment_line_obj.write(payment_line_ids,
                                   {'date': vals.get('date_scheduled', False)})
        elif vals.get('date_prefered', False) == 'due':
            vals.update({'date_scheduled': False})
            for order in self:
                for line in order.line_ids:
                    payment_line_obj.write([line.id],
                                           {'date': line.ml_maturity_date})
        elif vals.get('date_prefered', False) == 'now':
            vals.update({'date_scheduled': False})
            for order in self:
                for line in order.line_ids:
                    payment_line_ids.append(line.id)
            payment_line_obj.write(payment_line_ids, {'date': False})
        return super(PaymentRegister, self).write(vals)
