# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models


class EbillPostfinanceInvoiceMessage(models.Model):
    _inherit = "ebill.postfinance.invoice.message"

    def _get_payload_params_yb(self):
        params = super()._get_payload_params_yb()
        if self.invoice_id.invoice_payment_term_id.percent_discount:
            terms = self.invoice_id.invoice_payment_term_id
            params["discounts"].append(
                {
                    "percentage": terms.percent_discount,
                    "days": terms.days_discount,
                }
            )
        return params
