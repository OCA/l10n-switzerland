# -*- coding: utf-8 -*-

from odoo import api, models, _

class AccountMove(models.Model):
    _inherit = 'account.move'

    def _get_l10n_ch_isr_optical_amount(self):
        if len(self.invoice_payment_term_id.line_ids)>1:
            return "042"
        else:
            return super()._get_l10n_ch_isr_optical_amount()

    def split_total_amount(self):
        if len(self.invoice_payment_term_id.line_ids)>1:
            return ["",""]
        else:
            return super().split_total_amount()
