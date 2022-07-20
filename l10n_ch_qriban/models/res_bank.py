# Part of Odoo. See LICENSE file for full copyright and licensing details.
# flake8: noqa
import re

from odoo import api, fields, models, _
from odoo.addons.base_iban.models.res_partner_bank import (
    normalize_iban, pretty_iban, validate_iban
)
from odoo.exceptions import ValidationError
from odoo.tools.misc import mod10r


def sanitize_account_number(acc_number):
    if acc_number:
        return re.sub(r'\W+', '', acc_number).upper()
    return False


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    l10n_ch_qr_iban = fields.Char(
        string='QR-IBAN',
        help=(
            "Put the QR-IBAN here for your own bank accounts.  That way, you "
            "can still use the main IBAN in the Account Number while you will "
            "see the QR-IBAN for the barcode."
        ),
    )

    def _check_qr_iban_range(self, iban):
        if not iban or len(iban) < 9:
            return False
        iid_start_index = 4
        iid_end_index = 8
        iid = iban[iid_start_index:iid_end_index + 1]
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
        """ Tells whether or not this bank account has a QR-IBAN account
        number.
        QR-IBANs are specific identifiers used in Switzerland as references in
        QR-codes. They are formed like regular IBANs, but are actually
        something different.
        """
        self.ensure_one()

        iid_start_index = 4
        iid_end_index = 8
        iid = self.sanitized_acc_number[iid_start_index:iid_end_index+1]
        # Those values for iid are reserved for QR-IBANs only
        return (self.acc_type == 'iban' and re.match('\d+', iid)
                and 30000 <= int(iid) <= 31999) or self.l10n_ch_qr_iban

    @api.model
    def _is_qr_reference(self, reference):
        """ Checks whether the given reference is a QR-reference, i.e. it is
        made of 27 digits, the 27th being a mod10r check on the 26 previous
        ones.
        """
        return reference \
            and len(reference) == 27 \
            and re.match(r'\d+$', reference) \
            and reference == mod10r(reference[:-1])

    def validate_swiss_code_arguments(self,
                                      currency,
                                      debtor_partner,
                                      reference_to_check=''):
        # reference_to_check added as an optional parameter in order not to
        # break our stability policy.
        # For people having already installed the module, QRR won't be checked
        # until they update the module (as a change in the pdf report's xml
        # sets a value in reference_to_check).
        # '' is used as default, as an empty field will pass None value,
        # and we want to be able to distinguish between those cases
        def _partner_fields_set(partner):
            return partner.zip and \
                partner.city and \
                partner.country_id.code and \
                (self.partner_id.street or self.partner_id.street2)

        return _partner_fields_set(self.partner_id) and \
            _partner_fields_set(debtor_partner) and \
            (reference_to_check == '' or not self._is_qr_iban() or \
                self._is_qr_reference(reference_to_check))

    # fmt: on
