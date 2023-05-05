# copyright 2016 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _prepare_payment_line_vals(self, payment_order):
        vals = super()._prepare_payment_line_vals(payment_order)
        if (
            self.move_id
            and self.move_id._has_isr_ref()
            and self.move_id.partner_bank_id
        ):
            if self.move_id.partner_bank_id._is_qr_iban():
                vals["communication_type"] = "qrr"
            else:
                vals["local_instrument"] = "CH01"
                vals["communication_type"] = "isr"
            if vals["communication"]:
                vals["communication"] = vals["communication"].replace(" ", "")
        return vals
