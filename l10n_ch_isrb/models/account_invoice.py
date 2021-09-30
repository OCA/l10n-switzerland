# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _get_isrb_id_number(self):
        """Return ISR-B Customer ID"""
        self.ensure_one()
        partner_bank = self.partner_bank_id
        return partner_bank.l10n_ch_isrb_id_number or ""
