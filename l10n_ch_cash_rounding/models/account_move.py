# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    invoice_cash_rounding_id = fields.Many2one(
        "account.cash.rounding",
        compute="_compute_invoice_cash_rounding",
        states={"draft": [("readonly", False)]},
    )

    @api.depends("move_type", "currency_id")
    def _compute_invoice_cash_rounding(self):
        swiss_cash_rounding = self.env.ref(
            "l10n_ch_cash_rounding.swiss_cash_rounding", raise_if_not_found=False
        )
        if not swiss_cash_rounding:
            return
        for move in self:
            if move.move_type in [
                "out_invoice",
                "out_refund",
            ]:
                if move.currency_id == self.env.ref("base.CHF"):
                    move.invoice_cash_rounding_id = swiss_cash_rounding
