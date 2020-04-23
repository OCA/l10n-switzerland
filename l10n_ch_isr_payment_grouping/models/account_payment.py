# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, models

from odoo.addons.account.models.account_payment import MAP_INVOICE_TYPE_PARTNER_TYPE

class AbstractPayment(models.AbstractModel):
    _inherit = "account.abstract.payment"

    @api.model
    def is_multi(self, invoices):
        """Override computation of `multi` when multiple ISR are present"""
        multi = super().is_multi(invoices)
        # Look if we are mixin ISR ref invoices with vendor bills
        if multi:
            return multi
        isr_invoices = invoices.filtered(lambda rec:
                rec._is_isr_supplier_invoice())
        multi_isr = any(inv.reference != isr_invoices[0] for inv in isr_invoices)
        return multi_isr


class PaymentRegister(models.TransientModel):
    """Backport from v13 of extend of account.payment.register"""

    _inherit = "account.register.payments"

    def _prepare_communication(self, invoices):
        """Return a single ISR reference

        to avoid duplicate of the same number when multiple payments are done
        on the same reference. As those payments are grouped by reference,
        we want a unique reference in communication.

        """
        # Only the first invoice needs to be tested as the grouping ensure
        # invoice with same ISR are in the same group.
        if invoices[0]._is_isr_supplier_invoice():
            return invoices[0].reference
        else:
            return super()._prepare_communication(invoices)

    def _get_payment_group_key(self, inv):
        """Define group key to group invoices in payments.
        In case of ISR reference number on the supplier invoice
        the group rule must separate the invoices by payment refs.

        As such reference is structured. This is required to export payments
        to bank in batch.
        """
        if inv._is_isr_supplier_invoice():

            ref = inv.reference
            if inv.partner_id.type == 'invoice':
                partner_id = inv.partner_id.id
            else:
                partner_id = inv.commercial_partner_id.id
            account_id = inv.account_id.id
            invoice_type = MAP_INVOICE_TYPE_PARTNER_TYPE[inv.type]
            recipient_account = inv.partner_bank_id
            return (partner_id, account_id, invoice_type, recipient_account, ref)
        else:
            return super()._get_payment_group_key(inv)
