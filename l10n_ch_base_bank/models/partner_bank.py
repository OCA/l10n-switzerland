# Copyright 2012-2019 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class ResPartnerBank(models.Model):
    """Inherit res.partner.bank class in order to add swiss specific fields
    and state controls

    Statements:
    acc_type could be of 2 types:
        - iban
        - bank

    if acc_number given in 'iban' format just transform to iban format, but no
    further modification on it, and acc_type = 'iban'

    """

    _inherit = "res.partner.bank"

    def _get_ch_bank_from_iban(self):
        """Extract clearing number from CH iban to find the bank"""
        if self.acc_type != "iban" and self.acc_number[:2] != "CH":
            return False
        clearing = self.sanitized_acc_number[4:9].lstrip("0")
        return clearing and self.env["res.bank"].search(
            [("clearing", "=", clearing)], limit=1
        )

    @api.onchange("acc_number", "acc_type")
    def _onchange_acc_number_set_swiss_bank(self):
        """Deduce information from IBAN

        Bank is defined as:
        - Found bank by clearing when using iban
        """
        bank = self.bank_id
        if self.acc_type == "iban":
            bank = self._get_ch_bank_from_iban()
        self.bank_id = bank
