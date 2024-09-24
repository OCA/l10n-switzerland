from odoo import models


class ResPartnerBank(models.Model):
    _inherit = "res.partner.bank"

    def _eligible_for_qr_code(
        self, qr_method, debtor_partner, currency, raises_error=True
    ):
        if self.env.context.get("credit_control_run_print_report"):
            raises_error = False
        res = super()._eligible_for_qr_code(
            qr_method, debtor_partner, currency, raises_error=raises_error
        )
        return res
