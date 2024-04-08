# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from odoo import _, models

from odoo.addons.l10n_ch.models.res_bank import ResPartnerBank


class CustomResPartnerBank(models.Model):
    _inherit = "res.partner.bank"

    def _check_for_qr_code_errors(
        self,
        qr_method,
        amount,
        currency,
        debtor_partner,
        free_communication,
        structured_communication,
    ):

        # Override original method in case partner only has street3 defined
        def _partner_fields_set(partner):
            return (
                partner.zip
                and partner.city
                and partner.country_id.code
                and (partner.street or partner.street2 or partner.street3)
            )

        if qr_method == "ch_qr":
            if not _partner_fields_set(self.partner_id):
                return _(
                    # flake8: noqa
                    "The partner set on the bank account meant to receive the payment (%s) must have a complete postal address (street, zip, city and country).",
                    self.acc_number,
                )

            if debtor_partner and not _partner_fields_set(debtor_partner):
                return _(
                    "The partner must have a complete postal address (street, zip, city and country)."
                )

            if self.l10n_ch_qr_iban and not self._is_qr_reference(
                structured_communication
            ):
                return _(
                    "When using a QR-IBAN as the destination account of a QR-code, the payment reference must be a QR-reference."
                )
        # We bypass the original ResPartnerBank._check_for_qr_code_errors
        return super(ResPartnerBank, self)._check_for_qr_code_errors(
            qr_method,
            amount,
            currency,
            debtor_partner,
            free_communication,
            structured_communication,
        )
