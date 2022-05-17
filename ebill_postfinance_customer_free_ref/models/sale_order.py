# Copyright 2021-2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class SaleOrder(models.Model):

    _inherit = "sale.order"

    @api.depends("customer_order_number")
    def _compute_postfinance_ebill_client_order_ref(self):
        for order in self:
            order.postfinance_ebill_client_order_ref = order.customer_order_number
