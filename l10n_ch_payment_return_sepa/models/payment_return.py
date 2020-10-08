# Copyright 2020 Emanuel Cino <ecino@compassion.ch>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PaymentReturn(models.Model):
    _inherit = "payment.return"

    payment_order_id = fields.Many2one(
        "account.payment.order", "Originating Payment order")
