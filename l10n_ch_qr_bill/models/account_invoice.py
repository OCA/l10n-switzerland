# -*- coding: utf-8 -*-
# Copyright 2019-2020 Odoo
# Copyright 2019-2020 Camptocamp SA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import re

import werkzeug.urls

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.misc import mod10r
from odoo.addons.base.res.res_bank import sanitize_account_number

MSG_INCOMPLETE_PARTNER_ADDR = _(
    "- Partner address is incomplete, it must contain name, street, zip, city"
    " and country. Country must be Switzerland"
)

MSG_INCOMPLETE_COMPANY_ADDR = _(
    "- Company address is incomplete, it must contain name, street, zip, city"
    " and country. Country must be Switzerland"
)

MSG_NO_BANK_ACCOUNT = _(
    "- Invoice's 'Bank Account' is empty. You need to create or select a valid"
    " IBAN or QR-IBAN account"
)

MSG_BAD_QRR = _(
    "- With a QR-IBAN a valid QRR must be used."
)

ERROR_MESSAGES = {
    "incomplete_partner_address": MSG_INCOMPLETE_PARTNER_ADDR,
    "incomplete_company_address": MSG_INCOMPLETE_COMPANY_ADDR,
    "no_bank_account": MSG_NO_BANK_ACCOUNT,
    "bad_qrr": MSG_BAD_QRR,
}


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    l10n_ch_qrr = fields.Char(
        compute='_compute_l10n_ch_qrr',
        store=True,
        help='The reference QRR associated with this invoice',
    )

    l10n_ch_qrr_spaced = fields.Char(
        compute='_compute_l10n_ch_qrr_spaced',
        help=(
            "Reference QRR split in blocks of 5 characters (right-justified),"
            "to generate QR-bill report."
        ),
    )
    # This field is used in the "invisible" condition field of the 'Print QRR' button.
    l10n_ch_currency_name = fields.Char(
        related='currency_id.name',
        readonly=True,
        string="Currency Name",
        help="The name of this invoice's currency",
    )
    l10n_ch_qrr_sent = fields.Boolean(
        default=False,
        help=(
            "Boolean value telling whether or not the QRR corresponding to"
            " this invoice has already been printed or sent by mail.",
        ),
    )

    @api.model
    def _get_reference_type(self):
        res = super(AccountInvoice, self)._get_reference_type()
        return res + [('QRR', _('Swiss Reference QRR'))]

    def _get_qrr_prefix(self):
        """Hook to add a customized prefix"""
        self.ensure_one()
        return ''

    @api.depends('number', 'name')
    def _compute_l10n_ch_qrr(self):
        r""" Compute a QRR reference

        QRR is the replacement of ISR
        The QRR reference number is 27 characters long.

        To generate the QRR reference, the we use the invoice sequence number,
        removing each of its non-digit characters, and pad the unused spaces on
        the left of this number with zeros.
        The last digit is a checksum (mod10r).

        The reference is free but for the last
        digit which is a checksum.
        If shorter than 27 digits, it is filled with zeros on the left.

        e.g.

            120000000000234478943216899
            \________________________/|
                     1                2
            (1) 12000000000023447894321689 | reference
            (2) 9: control digit for identification number and reference

        """
        for record in self:
            if record.has_qrr():
                record.l10n_ch_qrr = record.name
            elif record.number:
                prefix = record._get_qrr_prefix()
                invoice_ref = re.sub(r'[^\d]', '', record.number)
                # keep only the last digits if it exceed boundaries
                full_len = len(prefix) + len(invoice_ref)
                extra = full_len - 26
                if extra > 0:
                    invoice_ref = invoice_ref[extra:]
                internal_ref = invoice_ref.zfill(26 - len(prefix))
                record.l10n_ch_qrr = mod10r(prefix + internal_ref)
            else:
                record.l10n_ch_qrr = False

    @api.depends('l10n_ch_qrr')
    def _compute_l10n_ch_qrr_spaced(self):
        def _space_qrr(ref):
            to_treat = ref
            res = ''
            while to_treat:
                res = to_treat[-5:] + res
                to_treat = to_treat[:-5]
                if to_treat:
                    res = ' ' + res
            return res

        for record in self:
            spaced_qrr = False
            if record.l10n_ch_qrr:
                spaced_qrr = _space_qrr(record.l10n_ch_qrr)
            record.l10n_ch_qrr_spaced = spaced_qrr

    def _get_communications(self):
        if self.has_qrr():
            structured_communication = self.l10n_ch_qrr
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
        # and must then be 27 characters-long, with mod10r check digit as the 27th one,
        # just like ISR number for invoices)
        reference_type = 'NON'
        reference = ''
        if self.has_qrr():
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

        # use quiet to remove blank around the QR and make it easier to place it
        return '/report/qrcode/?value=%s&width=%s&height=%s&bar_border=0' % (
            werkzeug.urls.url_quote_plus('\n'.join(qr_code_vals)),
            256,
            256,
        )

    def _get_partner_address_lines(self, partner):
        """ Returns a tuple of two elements containing the address lines to use
        for this partner. Line 1 contains the street and number, line 2 contains
        zip and city. Those two lines are limited to 70 characters
        """
        streets = [partner.street, partner.street2]
        line_1 = ' '.join(filter(None, streets))
        line_2 = partner.zip + ' ' + partner.city
        return line_1[:70], line_2[:70]

    @api.model
    def _is_qrr(self, reference):
        """ Checks whether the given reference is a QR-reference, i.e. it is
        made of 27 digits, the 27th being a mod10r check on the 26 previous ones.
        """
        return (
            reference
            and len(reference) == 27
            and re.match(r'\d+$', reference)
            and reference == mod10r(reference[:-1])
        )

    def validate_swiss_code_arguments(self):
        # TODO do checks separately
        reference_to_check = self.name

        def _partner_fields_set(partner):
            return (
                partner.zip
                and partner.city
                and partner.country_id.code
                and (partner.street or partner.street2)
            )

        self.errors = []
        if not _partner_fields_set(self.partner_id):
            self.errors.append("incomplete_partner_address")
        if not self.partner_bank_id:
            self.errors.append("no_bank_account")
        elif not _partner_fields_set(self.partner_bank_id.partner_id):
            self.errors.append("incomplete_company_address")
        if (reference_to_check
                and self.partner_bank_id._is_qr_iban()
                and not self._is_qrr(reference_to_check)):
            self.errors.append("bad_qrr")

        return not self.errors

    def can_generate_qr_bill(self, returned_errors=None):
        """ Returns True if the invoice can be used to generate a QR-bill.
        """
        self.ensure_one()
        return self.validate_swiss_code_arguments()

    def print_ch_qr_bill(self):
        """ Triggered by the 'Print QR-bill' button.
        """
        self.ensure_one()

        if not self.can_generate_qr_bill():
            msg_error_list = "\n".join(ERROR_MESSAGES[e] for e in self.errors)
            raise ValidationError(
                _("You cannot generate the QR-bill.\n"
                  "Here is what is blocking:\n"
                  "{}").format(msg_error_list)
            )

        self.l10n_ch_qrr_sent = True
        return self.env['report'].get_action(
            self, 'l10n_ch_qr_bill.qr_report_main'
        )

    def has_qrr(self):
        """Check if this invoice has a valid QRR reference (for Switzerland)

        """
        return self._is_qrr(self.name)

    def _validate_qrr(self):
        partner_bank = self.partner_bank_id
        if partner_bank._is_qr_iban() and not self.has_qrr():
            raise ValidationError(
                _("""The payment reference is not a valid QR Reference.""")
            )
        return True

    def action_invoice_open(self):
        res = super(AccountInvoice, self).action_invoice_open()
        for rec in self:
            # Define reference once number has been generated
            if rec.type == "out_invoice":
                if not rec.name and rec.partner_bank_id._is_qr_iban():
                    rec.name = rec.l10n_ch_qrr
            rec._validate_qrr()
        return res
