# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def get_qr_amount(self):
        qr_dunning_fees_amounts = self.env.context.get("qr_dunning_fees_amounts", {})
        if self.id in qr_dunning_fees_amounts:
            return "{:,.2f}".format(qr_dunning_fees_amounts[self.id]).replace(
                ",", "\xa0"
            )
        else:
            return "{:,.2f}".format(self.amount_residual).replace(",", "\xa0")
