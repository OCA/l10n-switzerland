# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class SaleOrder(models.Model):

    _inherit = "sale.order"

    paynet_client_order_ref = fields.Char(compute="_compute_paynet_client_order_ref")

    @api.depends("client_order_ref")
    def _compute_paynet_client_order_ref(self):
        """Compute the customer reference order to allow for glue module."""
        for order in self:
            order.paynet_client_order_ref = order.client_order_ref
