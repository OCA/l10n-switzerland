# -*- coding: utf-8 -*-
# Copyright 2020 Camptocamp SA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def _propagate_qrr(self):
        """Prepare the propagation of QRR by copying it to transaction_id


        For suppliers invoices: the QRR reference is stored in `name`
        field of the invoice.

        For customers invoices: the QRR will be stored in `l10n_ch_qrr`
        but it will only be filled once the move is generated.

        """
        self.ensure_one()
        if self.partner_bank_id._is_qr_iban():
            if self.type in ('in_invoice', 'in_refund'):
                if self._is_qrr(self.reference):
                    self.transaction_id = self.reference.replace(" ", "")
            else:
                # Generate a placeholder as the QRR is not generated yet
                self.transaction_id = "_l10n_ch_qrr_{}".format(self.id)

    @api.multi
    def _post_propagate_qrr(self):
        """Replace the placeholders by the QRR"""
        MoveLine = self.env["account.move.line"]
        for inv in self:
            placeholder = "_l10n_ch_qrr_{}".format(inv.id)
            if inv.transaction_id and inv.transaction_id == placeholder:
                inv.transaction_id = inv.l10n_ch_qrr
                lines = MoveLine.search(
                    [("transaction_ref", "=", placeholder)]
                )
                lines.write({"transaction_ref": inv.l10n_ch_qrr})

    @api.multi
    def action_move_create(self):
        """Prepare the copy of the QRR in to transaction_id

        Which will be later transfered in `finalize_invoice_move_lines`
        to `transaction_ref` on `account.move.line`

        """
        for inv in self:
            inv._propagate_qrr()
        res = super(AccountInvoice, self).action_move_create()
        self._post_propagate_qrr()
        return res
