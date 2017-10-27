# -*- coding: utf-8 -*-
# © 2012-2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, api, exceptions, fields, models

class AccountInvoice(models.Model):
    """Inherit account.invoice in order to add bvr
    printing functionnalites. BVR is a Swiss payment vector"""

    _inherit = "account.invoice"

    @api.multi
    def print_bvr_with_slip(self):
        self.write({
            'sent': True
        })
        return self.env['report'].get_action(
            self, 'invoice_and_one_slip_per_page_from_invoice')

