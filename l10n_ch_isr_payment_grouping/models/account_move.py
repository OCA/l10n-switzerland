# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import re

from odoo import models
from odoo.tools.misc import mod10r


class AccountMove(models.Model):
    _inherit = "account.move"

    def _get_invoice_reference_ch_invoice(self):
        """ This sets ISR reference number which is generated based on
        customer's `Bank Account` and set it as `Payment Reference` of
        the invoice when invoice's journal is using Switzerland's
        communication standard
        """
        self.ensure_one()
        return self.l10n_ch_isr_number

    def _get_invoice_reference_ch_partner(self):
        """ This sets ISR reference number which is generated based on
        customer's `Bank Account` and set it as `Payment Reference` of the
        invoice when invoice's journal is using Switzerland's communication
        standard
        """
        self.ensure_one()
        return self.l10n_ch_isr_number

    def _is_isr_supplier_invoice(self):
        """Check for payments that a supplier invoice has a bank account
        that can issue ISR and that the reference is an ISR reference number"""
        # We consider a structured ref can only be in `reference` whereas in v13
        # it can be in 2 different fields
        ref = self.invoice_payment_ref or self.ref
        if (
            ref
            and self.invoice_partner_bank_id.is_isr_issuer()
            and re.match(r"^(\d{2,27}|\d{2}( \d{5}){5})$", ref)
        ):
            ref = ref.replace(" ", "")
            return ref == mod10r(ref[:-1])
        return False
