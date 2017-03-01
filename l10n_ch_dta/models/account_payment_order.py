# -*- coding: utf-8 -*-
# Copyright 2016 Braintec AG - Kumar Aberer <kumar.aberer@braintec-group.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, api


class AccountPaymentOrder(models.Model):
    _inherit = 'account.payment.order'

    @api.multi
    def generate_payment_file(self):
        """Creates the DTA file. That's the important code!"""
        self.ensure_one()
        if self.payment_mode_id.payment_method_id.code != 'DTA':
            return super(AccountPaymentOrder, self).generate_payment_file()

        # The following code is just so the existing wizard can be reused
        # without completely refactoring it
        wizard_obj = self.env['create.dta.wizard']
        ctx = dict(self.env.context)
        ctx.update({'active_id': self.id})
        ctx.update({'active_ids': self.ids})
        dta_filename, dta_file = wizard_obj.with_context(ctx).create_dta()

        return dta_file, dta_filename
