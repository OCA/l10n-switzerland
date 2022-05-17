# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class SaleOrder(models.Model):

    _inherit = "sale.order"

    @api.depends("customer_order_number")
    def _compute_paynet_client_order_ref(self):
        for order in self:
            order.paynet_client_order_ref = order.customer_order_number
