# copyright 2016 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _prepare_payment_line_vals(self, payment_order):
        vals = super()._prepare_payment_line_vals(payment_order)
        # swiss QRR validation is done on account.payment in version 18.0
        payment = self.env["account.payment"].new(
            {
                "payment_type": "outbound",
                "partner_id": self.move_id.partner_id,
                "memo": vals["communication"],
            }
        )
        if (
            self.move_id
            and self.move_id.partner_bank_id.l10n_ch_qr_iban
            and payment._l10n_ch_reference_is_valid(vals["communication"])
            and not payment.l10n_ch_reference_warning_msg
        ):
            vals["communication_type"] = "qrr"
            vals["communication"] = vals["communication"].replace(" ", "")
        return vals
