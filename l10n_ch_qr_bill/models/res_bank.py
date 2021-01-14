# -*- coding: utf-8 -*-
# Copyright 2019-2020 Odoo
# Copyright 2019-2020 Camptocamp SA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
import re

from odoo import api, fields, models, _
from odoo.addons.base_iban.models.res_partner_bank import (
    normalize_iban, pretty_iban, validate_iban
)
from odoo.addons.base.res.res_bank import sanitize_account_number
from odoo.exceptions import ValidationError


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    l10n_ch_qr_iban = fields.Char(
        string='QR-IBAN',
        help=(
            "Put the QR-IBAN here for your own bank accounts.  That way, you"
            " can still use the main IBAN in the Account Number while you will"
            " see the QR-IBAN for the barcode."
        )
    )

    @api.constrains('l10n_ch_qr_iban')
    def _check_ch_li_l10n_ch_qr_iban(self):
        """Validate QR-IBAN"""
        for record in self:
            self._validate_qr_iban(record.l10n_ch_qr_iban)

    def _check_qr_iban_range(self, iban):
        if not iban or len(iban) < 9:
            return False
        iid_start_index = 4
        iid_end_index = 8
        iid = iban[iid_start_index : iid_end_index + 1]
        # Those iid between 30000 and 31999 are reserved for QR-IBANs only
        return (re.match(r'\d+', iid)
                and 30000 <= int(iid) <= 31999)

    def _validate_qr_iban(self, qr_iban):
        if qr_iban and not qr_iban.startswith(('CH', 'LI')):
            raise ValidationError(_(
                "Not a valid Switzerland or Liechtenstein QR-IBAN."))
        # Check first if it's a valid IBAN.
        validate_iban(qr_iban)
        # We sanitize first so that _check_qr_iban_range()
        # can extract correct IID from IBAN to validate it.
        sanitized_qr_iban = sanitize_account_number(qr_iban)
        # Now, check if it's valid QR-IBAN (based on its IID).
        if not self._check_qr_iban_range(sanitized_qr_iban):
            raise ValidationError(_("QR-IBAN '%s' is invalid.") % qr_iban)
        return True

    @api.model
    def create(self, vals):
        if vals.get('l10n_ch_qr_iban'):
            self._validate_qr_iban(vals['l10n_ch_qr_iban'])
            iban = pretty_iban(normalize_iban(vals['l10n_ch_qr_iban']))
            vals['l10n_ch_qr_iban'] = iban
        return super(ResPartnerBank, self).create(vals)

    def write(self, vals):
        if vals.get('l10n_ch_qr_iban'):
            self._validate_qr_iban(vals['l10n_ch_qr_iban'])
            iban = pretty_iban(normalize_iban(vals['l10n_ch_qr_iban']))
            vals['l10n_ch_qr_iban'] = iban
        return super(ResPartnerBank, self).write(vals)

    def _is_qr_iban(self):
        """ Tells whether or not this bank account has a QR-IBAN account number.
        QR-IBANs are specific identifiers used in Switzerland as references in
        QR-codes. They are formed like regular IBANs, but are actually something
        different.

        """
        return (
            self.acc_type == "iban"
            and self.l10n_ch_qr_iban
            or (
                self._check_qr_iban_range(self.sanitized_acc_number) and
                self.sanitized_acc_number.startswith(('CH', 'LI'))
            )
        )
