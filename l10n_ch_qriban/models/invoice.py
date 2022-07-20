# Copyright 2020 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import re
import werkzeug.urls

from odoo import _, api, models


def sanitize_account_number(acc_number):
    if acc_number:
        return re.sub(r'\W+', '', acc_number).upper()
    return False


class AccountInvoice(models.Model):

    _inherit = "account.invoice"

    @api.model
    def _get_reference_type(self):
        res = super(AccountInvoice, self)._get_reference_type()
        return res + [('QRR', _('Swiss Reference QRR'))]

    def _need_isr_ref(self):
        """Uses hook of l10n_ch_fix_isr_reference module"""
        has_qriban = (
            self.partner_bank_id and
            self.partner_bank_id._is_qr_iban() or False
        )
        return has_qriban or super()._need_isr_ref()

    @api.model
    def space_qrr_reference(self, qrr_ref):
        """ Makes the provided QRR reference human-friendly, spacing its elements
        by blocks of 5 from right to left.
        """
        spaced_qrr_ref = ''
        # i is the index after the last index to consider in substrings
        i = len(qrr_ref)
        while i > 0:
            spaced_qrr_ref = qrr_ref[max(i-5, 0):i] + ' ' + spaced_qrr_ref
            i -= 5

        return spaced_qrr_ref

    def _get_communications(self):
        is_qrr = self.partner_bank_id._is_qr_iban()
        if is_qrr:
            structured_communication = self.reference
            free_communication = ''
        else:
            structured_communication = ''
            free_communication = self.name
        free_communication = free_communication or self.number

        additional_info = ""
        if free_communication:
            additional_info = (
                (free_communication[:137] + '...')
                if len(free_communication) > 140
                else free_communication
            )

        # Compute reference type (empty by default, only mandatory for QR-IBAN,
        # and must then be 27 characters-long, with mod10r check digit as the
        # 27th one, just like ISR number for invoices)
        reference_type = 'NON'
        reference = ''
        if is_qrr:
            # _check_for_qr_code_errors ensures we can't have a QR-IBAN
            # without a QR-reference here
            reference_type = 'QRR'
            reference = structured_communication
        return reference_type, reference, additional_info

    def _prepare_swiss_code_url_vals(self):

        reference_type, reference, additional_info = self._get_communications()

        creditor = self.company_id.partner_id
        debtor = self.commercial_partner_id

        creditor_addr_1, creditor_addr_2 = self._get_partner_address_lines(
            creditor
        )
        debtor_addr_1, debtor_addr_2 = self._get_partner_address_lines(debtor)

        amount = '{:.2f}'.format(self.residual)
        acc_number = self.partner_bank_id.sanitized_acc_number

        # If there is a QR IBAN we use it for the barcode instead of the
        # account number
        qr_iban = self.partner_bank_id.l10n_ch_qr_iban
        if qr_iban:
            acc_number = sanitize_account_number(qr_iban)

        # fmt: off
        qr_code_vals = [
            'SPC',                      # QR Type
            '0200',                     # Version
            '1',                        # Coding Type
            acc_number,                 # IBAN
                                        # Creditor
            'K',                        # - Address Type
            creditor.name[:70],         # - Name
            creditor_addr_1,            # - Address Line 1
            creditor_addr_2,            # - Address Line 2
            '',                         # - Postal Code (not used in type K)
            '',                         # - City (not used in type K)
            creditor.country_id.code,   # - Country
                                        # Ultimate Creditor
            '',                         # - Address Type
            '',                         # - Name
            '',                         # - Address Line 1
            '',                         # - Address Line 2
            '',                         # - Postal Code
            '',                         # - Town
            '',                         # - Country
            amount,                     # Amount
            self.currency_id.name,      # Currency
                                        # Ultimate Debtor
            'K',                        # - Address Type
            debtor.name[:70],           # - Name
            debtor_addr_1,              # - Address Line 1
            debtor_addr_2,              # - Address Line 2
            '',                         # - Postal Code (not used in type K)
            '',                         # - City (not used in type K)
            debtor.country_id.code,     # - Country
            reference_type,             # Reference Type
            reference,                  # Reference
            additional_info,            # Unstructured Message
            'EPD',                      # Mandatory trailer part
            '',                         # Bill information
        ]
        # fmt: on
        return qr_code_vals

    @api.multi
    def build_swiss_code_url(self):

        self.ensure_one()

        qr_code_vals = self._prepare_swiss_code_url_vals()

        # use quiet to remove blank around the QR and make it easier to place 
        # it
        return '/report/qrcode/?value=%s&width=%s&height=%s&bar_border=0' % (
            werkzeug.urls.url_quote_plus('\n'.join(qr_code_vals)),
            256,
            256,
        )

    def _get_partner_address_lines(self, partner):
        """ Returns a tuple of two elements containing the address lines to use
        for this partner. Line 1 contains the street and number, line 2 
        contains zip and city. Those two lines are limited to 70 characters
        """
        streets = [partner.street, partner.street2]
        line_1 = ' '.join(filter(None, streets))
        line_2 = partner.zip + ' ' + partner.city
        return line_1[:70], line_2[:70]
