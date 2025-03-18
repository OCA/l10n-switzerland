# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)


from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def can_generate_qr_bill(self):
        # Originally method returns True if the invoice can be used to generate
        # a QR-bill. We add context key dependency to prevent generation of
        # attachment inside
        # https://github.com/odoo/odoo/blob/15.0/addons/l10n_ch/models/mail_template.py#L12
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


class AccountMoveSend(models.TransientModel):
    _inherit = "account.move.send"

    def action_send_and_print(self):
        # override to update context with new key
        return super(
            AccountMoveSend, self.with_context(invoice_report_no_attachment=True)
        ).action_send_and_print()
