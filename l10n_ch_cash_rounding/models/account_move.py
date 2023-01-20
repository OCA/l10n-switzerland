# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    invoice_cash_rounding_id = fields.Many2one(
        "account.cash.rounding",
        readonly=False,
        compute="_compute_invoice_cash_rounding",
        states={},
    )

    @api.depends("move_type", "currency_id")
    def _compute_invoice_cash_rounding(self):
        for move in self:
            if move.move_type in [
                "out_invoice",
                "out_refund",
            ]:
                if move.currency_id.id == self.env.ref("base.CHF").id:
                    move.invoice_cash_rounding_id = self.env.ref(
                        "l10n_ch_cash_rounding.swiss_cash_rounding"
                    ).id
                else:
                    move.invoice_cash_rounding_id = False
