# Copyright 2024 Camptocamp (<https://www.camptocamp.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class ResPartnerBank(models.Model):
    _inherit = "res.partner.bank"

    def _l10n_ch_get_qr_vals(
        self,
        amount,
        currency,
        debtor_partner,
        free_communication,
        structured_communication,
    ):
        res = super()._l10n_ch_get_qr_vals(
            amount,
            currency,
            debtor_partner,
            free_communication,
            structured_communication,
        )
        if self.env.context.get("qr_bill_without_amount", {}).get(free_communication):
            # Amount position
            res[18] = ""
        return res
