# Copyright 2023 Camptocamp SA (https://www.camptocamp.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def partner_banks_to_show(self):
        # OVERRIDE to add more results if base method does not give any
        res = super().partner_banks_to_show()
        return res or self.journal_id.bank_account_id
