# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)


from odoo import api, models


class AccountMove(models.Model):
    _inherit = "account.move"

    # add context key dependency to prevent generation of attachment inside
    # https://github.com/odoo/odoo/blob/13.0/addons/l10n_ch/models/mail_template.py#L12
    @api.depends_context("invoice_report_no_attachment")
    def _compute_l10n_ch_isr_valid(self):
        if self.env.context.get("invoice_report_no_attachment", False):
            self.update({"l10n_ch_isr_valid": False})
        else:
            super()._compute_l10n_ch_isr_valid()

    def can_generate_qr_bill(self):
        # Originally method returns True if the invoice can be used to generate a QR-bill.
        # We add context key dependency to prevent generation of attachment inside
        # https://github.com/odoo/odoo/blob/13.0/addons/l10n_ch/models/mail_template.py#L12
        self.ensure_one()
        if self.env.context.get("invoice_report_no_attachment", False):
            return False
        return not self.env.ref(
            "l10n_ch.l10n_ch_swissqr_template"
        ).inherit_id and self.invoice_partner_bank_id.validate_swiss_code_arguments(
            self.invoice_partner_bank_id.currency_id,
            self.partner_id,
            self.invoice_payment_ref,
        )

    def action_invoice_sent(self):
        # override to update context with new key
        action = super().action_invoice_sent()
        action["context"] = dict(
            action.get("context", {}), invoice_report_no_attachment=True
        )
        return action


class AccountInvoiceSend(models.TransientModel):
    _inherit = "account.invoice.send"

    def send_and_print_action(self):
        # override to update context with new key
        return super(
            AccountInvoiceSend, self.with_context(invoice_report_no_attachment=True)
        ).send_and_print_action()
