# copyright 2016 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, models
from odoo.exceptions import UserError


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _prepare_payment_line_vals(self, payment_order):
        vals = super()._prepare_payment_line_vals(payment_order)
        if self.payment_order.payment_method_id.pain_version in [
            "pain.001.001.03.ch.02",
            "pain.008.001.02.ch.01",
        ]:

            if not self.partner_bank_id:
                raise UserError(
                    _(
                        "For pain.001.001.03.ch.02 a recipient bank account must be set on "
                        "move :  '%s'"
                    )
                    % (self.move_id.name)
                )

            if self.partner_bank_id._is_qr_iban() and not self.move_id._has_isr_ref():
                raise UserError(
                    _(
                        "For pain.001.001.03.ch.02 QR-IBAN payments, "
                        "a QR-Reference is required on the move :  '%s'"
                    )
                    % (self.move_id.name)
                )

            if (
                self.partner_bank_id._is_isr_issuer()
                and not self.move_id._has_isr_ref()
            ):
                raise UserError(
                    _(
                        "For pain.001.001.03.ch.02 ISR payments, "
                        "an ISR is required on the move :  '%s'"
                    )
                    % (self.move_id.name)
                )

            vals["communication"] = self.move_id.payment_reference or self.move_id.ref
            if self.partner_bank_id._is_isr_issuer():
                vals["local_instrument"] = "CH01"
                vals["communication_type"] = "isr"

            elif self.partner_bank_id._is_qr_iban():
                vals["communication_type"] = "qrr"

            if vals["communication"]:
                vals["communication"] = vals["communication"].replace(" ", "")

        return vals
