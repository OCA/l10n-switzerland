# -*- coding: utf-8 -*-
# Copyright 2016 Braintec AG - Kumar Aberer <kumar.aberer@braintec-group.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class AccountPaymentLine(models.Model):
    _inherit = 'account.payment.line'
    _description = 'Payment Lines'

    communication_type = fields.Selection(selection_add=[('bvr', 'bvr')])

    def invoice_reference_type2communication_type(self):
        res = super(AccountPaymentLine,
                    self).invoice_reference_type2communication_type()
        res.update({'bvr': 'bvr'})
        return res
