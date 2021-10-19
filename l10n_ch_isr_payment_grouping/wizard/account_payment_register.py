# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, models


class PaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    @api.model
    def _get_batch_communication(self, batch_result):
        """Return a single ISR reference
        to avoid duplicate of the same number when multiple payments are done
        on the same reference. As those payments are grouped by reference,
        we want a unique reference in communication.
        """
        # Only the first invoice needs to be tested as the grouping ensure
        # invoice with same ISR are in the same group.
        invoice = batch_result["lines"][0].move_id
        if invoice._is_isr_supplier_invoice():
            return invoice.payment_reference or invoice.ref
        else:
            return super()._get_batch_communication(batch_result)

    def _get_line_batch_key(self, line):
        move = line.move_id
        result = super()._get_line_batch_key(line)
        if move._is_isr_supplier_invoice():
            result.update(
                {
                    "payment_reference": move.payment_reference or line.ref,
                }
            )
        return result
