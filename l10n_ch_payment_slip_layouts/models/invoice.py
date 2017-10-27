# -*- coding: utf-8 -*-
# Copyright 2015 Camptocamp SA - Nicolas Bessi
# Copyright 2017 Jean Respen
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, models


class AccountInvoice(models.Model):
    """Inherit account.invoice in order to add invoice and bvr
    printing functionnalites. BVR is a Swiss payment vector"""

    _inherit = "account.invoice"

    @api.multi
    def print_bvr_with_slip(self):
        self.write({
            'sent': True
        })
        return self.env['report'].get_action(
            self, 'invoice_and_one_slip_per_page_from_invoice')
