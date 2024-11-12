# Copyright 2024 Camptocamp (<https://www.camptocamp.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    qr_bill_amount = fields.Char(
        compute="_compute_qr_bill_amount",
    )

    @api.depends("amount_residual")
    def _compute_qr_bill_amount(self):
        for move in self:
            if move.payment_mode_id.qr_bill_without_amount:
                move.qr_bill_amount = ""
            else:
                move.qr_bill_amount = "{:,.2f}".format(move.amount_residual).replace(
                    ",", "\xa0"
                )
