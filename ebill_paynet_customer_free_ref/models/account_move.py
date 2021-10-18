# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def get_paynet_other_reference(self):
        ref = super().get_paynet_other_reference()
        for order in self.invoice_line_ids.sale_line_ids.mapped("order_id"):
            if order.customer_order_free_ref:
                ref.append({"type": "CR", "no": order.customer_order_free_ref})
        return ref
