# Part of Odoo. See LICENSE file for full copyright and licensing details.
# flake8: noqa
import re
import werkzeug.urls

from odoo import api, fields, models, _
from odoo.addons.base_iban.models.res_partner_bank import (
    normalize_iban, pretty_iban, validate_iban
)
from odoo.addons.base.models.res_bank import sanitize_account_number
from odoo.exceptions import ValidationError


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    l10n_ch_qr_iban = fields.Char(
        string='QR-IBAN',
        help=(
            "Put the QR-IBAN here for your own bank accounts.  That way, you can"
            " still use the main IBAN in the Account Number while you will see the"
            " QR-IBAN for the barcode."
        ),
    )

    def _check_qr_iban_range(self, iban):
        if not iban or len(iban) < 9:
            return False
        iid_start_index = 4
        iid_end_index = 8
        iid = iban[iid_start_index : iid_end_index + 1]
        return (
            re.match(r'\d+', iid)
            # Those values for iid are reserved for QR-IBANs only
            and 30000 <= int(iid) <= 31999
        )

    def _validate_qr_iban(self, qr_iban):
        # Check first if it's a valid IBAN.
        validate_iban(qr_iban)
        # We sanitize first so that _check_qr_iban_range() can
        # extract correct IID from IBAN to validate it.
        sanitized_qr_iban = sanitize_account_number(qr_iban)
        # Now, check if it's valid QR-IBAN (based on its IID).
        if not self._check_qr_iban_range(sanitized_qr_iban):
            raise ValidationError(_("QR-IBAN '%s' is invalid.") % qr_iban)
        return True

    @api.model
    def create(self, vals):
        if vals.get('l10n_ch_qr_iban'):
            self._validate_qr_iban(vals['l10n_ch_qr_iban'])
            vals['l10n_ch_qr_iban'] = pretty_iban(
                normalize_iban(vals['l10n_ch_qr_iban'])
            )
        return super().create(vals)

    def write(self, vals):
        if vals.get('l10n_ch_qr_iban'):
            self._validate_qr_iban(vals['l10n_ch_qr_iban'])
            vals['l10n_ch_qr_iban'] = pretty_iban(
                normalize_iban(vals['l10n_ch_qr_iban'])
            )
        return super().write(vals)

    def _is_qr_iban(self):
        return super()._is_qr_iban() or self.l10n_ch_qr_iban

    # fmt: off
    # Overwrite of official odoo code
    def build_swiss_code_vals(
            self, amount, currency_name, not_used_anymore_1, debtor_partner,
            not_used_anymore_2, structured_communication, free_communication
    ):
        vals = super().build_swiss_code_vals(amount, currency_name, not_used_anymore_1, debtor_partner, not_used_anymore_2, structured_communication, free_communication)
        if self.l10n_ch_qr_iban:
            acc_number = sanitize_account_number(self.l10n_ch_qr_iban)
            vals = vals[:3]+[acc_number]+vals[4:]
        return vals
    # fmt: on
