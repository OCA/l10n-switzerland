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
    @api.model
    def build_swiss_code_url(
            self, amount, currency_name, not_used_anymore_1, debtor_partner,
            not_used_anymore_2, structured_communication, free_communication
    ):
        comment = ""
        if free_communication:
            comment = (free_communication[:137] + '...') if len(free_communication) > 140 else free_communication

        creditor_addr_1, creditor_addr_2 = self._get_partner_address_lines(self.partner_id)
        debtor_addr_1, debtor_addr_2 = self._get_partner_address_lines(debtor_partner)

        # Compute reference type (empty by default, only mandatory for QR-IBAN,
        # and must then be 27 characters-long, with mod10r check digit as the 27th one,
        # just like ISR number for invoices)
        reference_type = 'NON'
        reference = ''
        if self._is_qr_iban():
            # _check_for_qr_code_errors ensures we can't have a QR-IBAN
            # without a QR-reference here
            reference_type = 'QRR'
            reference = structured_communication

        # If there is a QR IBAN we use it for the barcode instead of the account number
        acc_number = self.sanitized_acc_number
        if self.l10n_ch_qr_iban:
            acc_number = sanitize_account_number(self.l10n_ch_qr_iban)

        qr_code_vals = [
            'SPC',                                                # QR Type
            '0200',                                               # Version
            '1',                                                  # Coding Type
            acc_number,                                           # IBAN
            'K',                                                  # Creditor Address Type
            (self.acc_holder_name or self.partner_id.name)[:71],  # Creditor Name
            creditor_addr_1,                                      # Creditor Address Line 1
            creditor_addr_2,                                      # Creditor Address Line 2
            '',                                                   # Creditor Postal Code (empty, since we're using combined addres elements)
            '',                                                   # Creditor Town (empty, since we're using combined addres elements)
            self.partner_id.country_id.code,                      # Creditor Country
            '',                                                   # Ultimate Creditor Address Type
            '',                                                   # Name
            '',                                                   # Ultimate Creditor Address Line 1
            '',                                                   # Ultimate Creditor Address Line 2
            '',                                                   # Ultimate Creditor Postal Code
            '',                                                   # Ultimate Creditor Town
            '',                                                   # Ultimate Creditor Country
            '{:.2f}'.format(amount),                              # Amount
            currency_name,                                        # Currency
            'K',                                                  # Ultimate Debtor Address Type
            debtor_partner.name[:71],                             # Ultimate Debtor Name
            debtor_addr_1,                                        # Ultimate Debtor Address Line 1
            debtor_addr_2,                                        # Ultimate Debtor Address Line 2
            '',                                                   # Ultimate Debtor Postal Code (not to be provided for address type K)
            '',                                                   # Ultimate Debtor Postal City (not to be provided for address type K)
            debtor_partner.country_id.code,                       # Ultimate Debtor Postal Country
            reference_type,                                       # Reference Type
            reference,                                            # Reference
            comment,                                              # Unstructured Message
            'EPD',                                                # Mandatory trailer part
        ]

        return '/report/barcode/?type=%s&value=%s&width=%s&height=%s&humanreadable=1' % (
            'QR_quiet', werkzeug.urls.url_quote_plus('\n'.join(qr_code_vals)), 256, 256
        )
    # fmt: on
