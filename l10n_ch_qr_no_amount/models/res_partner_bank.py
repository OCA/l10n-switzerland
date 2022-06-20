from odoo import models


class ResPartnerBank(models.Model):

    _inherit = "res.partner.bank"

    def _prepare_swiss_code_url_vals(
        self, amount, currency_name, debtor_partner, reference_type, reference, comment
    ):
        res = super()._prepare_swiss_code_url_vals(
            amount, currency_name, debtor_partner, reference_type, reference, comment
        )
        if len(self.invoice_payment_term_id.line_ids) > 1:
            res = self._remove_swiss_code_amount(res)
        return res

    def _remove_swiss_code_amount(self, values_list):
        # 18 is the position of amount in returned list
        values_list[18] = ""
        return values_list
