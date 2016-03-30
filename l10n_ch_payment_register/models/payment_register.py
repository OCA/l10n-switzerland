# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2015 brain-tec AG (http://www.braintec-group.com)
#    All Right Reserved
#
#    License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
##############################################################################

import time
from openerp import models, fields, api


class PaymentRegister(models.Model):
    _name = 'payment.register'
    _description = 'Payment Register'
    _rec_name = 'reference'
    _order = 'create_date'

    @api.depends('line_ids.amount')
    def _compute_total(self):
        for payment_register in self:
            payment_register.total = sum(payment_register.
                                         mapped('line_ids.amount'))

    date_scheduled = fields.Date('Scheduled Date',
                                 states={'done': [('readonly', True)]},
                                 help='Select a date if you have chosen '
                                 'Preferred Date to be fixed.')

    reference = fields.Char('Reference', required=1,
                            states={'done': [('readonly', True)]},
                            default=lambda self:
                            self.env['ir.sequence'].get('payment.register'),
                            copy=False)

    mode = fields.Many2one('payment.mode', 'Payment Mode', index=True,
                           required=1, states={'done': [('readonly', True)]},
                           help='Select the Payment Mode to be applied.')

    state = fields.Selection([('draft', 'Draft'),
                              ('cancel', 'Cancelled'),
                              ('open', 'Confirmed'),
                              ('done', 'Done')], 'Status', index=True,
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
                  help="Choose an option for the Payment Order: 'Fixed' "
                       "stands for a date specified by you.'Directly' stands "
                       "for the direct execution. 'Due date' stands for the "
                       "scheduled date of execution.")

    date_created = fields.Date('Creation Date', readonly=True,
                               default=fields.Date.today)

    date_done = fields.Date('Execution Date', readonly=True)

    company_id = fields.Many2one('res.company', related='mode.company_id',
                                 string='Company', store=True, readonly=True)

    @api.multi
    def set_to_draft(self):
        self.write({'state': 'draft'})
        return True

    @api.multi
    def set_to_confirmed(self):
        self.write({'state': 'open'})
        return True

    @api.multi
    def set_done(self):
        self.write({'date_done': time.strftime('%Y-%m-%d'), 'state': 'done'})
        return True

    @api.multi
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
