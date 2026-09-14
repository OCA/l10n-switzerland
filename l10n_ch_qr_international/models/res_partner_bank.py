# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import _, models


class ResPartnerBank(models.Model):
    _inherit = "res.partner.bank"

    def _get_error_messages_for_qr(self, qr_method, debtor_partner, currency):
        # Copy of internal function from
        #  l10n_ch.models.res_bank.py::ResPartnerBank._get_error_messages_for_qr
        #  to remove the check on debtor_partner's country
        # TODO: When migrating to v18.0, we can override _l10n_ch_qr_debtor_check
        #  instead
        def _get_error_for_ch_qr():
            error_messages = [
                _(
                    "The Swiss QR code could not be generated for the following"
                    " reason(s):"
                )
            ]
            if self.acc_type != "iban":
                error_messages.append(_("The account type isn't QR-IBAN or IBAN."))
            if currency.id not in (
                self.env.ref("base.EUR").id,
                self.env.ref("base.CHF").id,
            ):
                error_messages.append(_("The currency isn't EUR nor CHF."))
            return "\r\n".join(error_messages) if len(error_messages) > 1 else None

        res = super()._get_error_messages_for_qr(qr_method, debtor_partner, currency)
        if (
            res
            and qr_method == "ch_qr"
            and debtor_partner.commercial_partner_id.force_swiss_qr_invoice
            and not _get_error_for_ch_qr()
        ):
            return None
        return res
