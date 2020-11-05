# Copyright 2020 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import re

from odoo import api, models
from odoo.tools import mod10r


l10n_ch_ISR_NUMBER_LENGTH = 27
l10n_ch_ISR_ID_NUM_LENGTH = 6


class AccountInvoice(models.Model):

    _inherit = "account.invoice"

    def _get_isrb_id_number(self):
        """Return ISR-B Customer ID"""
        self.ensure_one()
        partner_bank = self.partner_bank_id
        return (
            hasattr(partner_bank, "l10n_ch_isrb_id_number") and
            partner_bank.l10n_ch_isrb_id_number or ""
        )

    def _need_isr_ref(self):
        return bool(self.l10n_ch_isr_subscription)

    @api.depends('name', 'partner_bank_id.l10n_ch_postal')
    def _compute_l10n_ch_isr_number(self):
        r"""Generates the ISR or QRR reference

        An ISR references are 27 characters long.
        QRR is a recycling of ISR for QR-bills. Thus works the same.

        The invoice sequence number is used, removing each of its non-digit characters,
        and pad the unused spaces on the left of this number with zeros.
        The last digit is a checksum (mod10r).

        There are 2 types of references:

        * ISR (Postfinance)

            The reference is free but for the last
            digit which is a checksum.
            If shorter than 27 digits, it is filled with zeros on the left.

            e.g.

                120000000000234478943216899
                \________________________/|
                         1                2
                (1) 12000000000023447894321689 | reference
                (2) 9: control digit for identification number and reference

        * ISR-B (Indirect through a bank, requires a customer ID)

            In case of ISR-B The firsts digits (usually 6), contain the customer ID
            at the Bank of this ISR's issuer.
            The rest (usually 20 digits) is reserved for the reference plus the
            control digit.
            If the [customer ID] + [the reference] + [the control digit] is shorter
            than 27 digits, it is filled with zeros between the customer ID till
            the start of the reference.

            e.g.

                150001123456789012345678901
                \____/\__________________/|
                   1           2          3
                (1) 150001 | id number of the customer (size may vary)
                (2) 12345678901234567890 | reference
                (3) 1: control digit for identification number and reference
        """
        for record in self:

            if (record._need_isr_ref()) and record.number:
                id_number = record._get_isrb_id_number()
                if id_number:
                    id_number = id_number.zfill(l10n_ch_ISR_ID_NUM_LENGTH)
                invoice_ref = re.sub(r'[^\d]', '', record.number)
                # keep only the last digits if it exceed boundaries
                full_len = len(id_number) + len(invoice_ref)
                ref_payload_len = l10n_ch_ISR_NUMBER_LENGTH - 1
                extra = full_len - ref_payload_len
                if extra > 0:
                    invoice_ref = invoice_ref[extra:]
                internal_ref = invoice_ref.zfill(ref_payload_len - len(id_number))
                record.l10n_ch_isr_number = mod10r(id_number + internal_ref)
            else:
                record.l10n_ch_isr_number = False
