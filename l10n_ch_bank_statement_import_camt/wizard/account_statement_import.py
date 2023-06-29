# Copyright 2023 Compassion CH
# Licence LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).

import logging

from odoo import api, fields, models

from odoo.addons.base.models.res_bank import sanitize_account_number

logger = logging.getLogger(__name__)


class ResPartnerBank(models.Model):
    _inherit = "res.partner.bank"

    sanitized_qr_iban = fields.Char(compute="_compute_sanitized_acc_number", store=True)

    @api.depends("l10n_ch_qr_iban")
    def _compute_sanitized_acc_number(self):
        for bank in self:
            bank.sanitized_qr_iban = (
                sanitize_account_number(bank.l10n_ch_qr_iban)
                if bank.l10n_ch_qr_iban
                else False
            )


class AccountStatementImport(models.TransientModel):
    _inherit = "account.statement.import"
    _description = "Import Bank Statement Files"

    qriban_no = fields.Char(readonly=True, invisible=True)

    def _check_parsed_data(self, stmts_vals):
        """Retrieve the information from the statement vals and take it out of the datas"""
        if stmts_vals:
            if stmts_vals[0].get("camt_headers"):
                stmts_vals[0].pop("camt_headers")
                ntry_ref = stmts_vals[0].pop("ntryRef")
                if ntry_ref:
                    self.write({"qriban_no": ntry_ref})
        return super(AccountStatementImport, self)._check_parsed_data(stmts_vals)

    @api.model
    def _match_journal(self, account_number, currency):
        """
        We want to match the journal that are with qr iban in some cases
        (parsing camt54)
        """
        journal = super()._match_journal(account_number, currency)
        journal_obj = self.env["account.journal"]
        journal_qriban = self.qriban_no
        if journal_qriban:
            company = self.env.company
            bank_account = self.env["res.partner.bank"].search(
                [
                    ("partner_id", "=", company.partner_id.id),
                    ("sanitized_qr_iban", "=", sanitize_account_number(journal_qriban)),
                ],
                limit=1,
            )
            journal = journal_obj.search(
                [
                    ("type", "=", "bank"),
                    ("bank_account_id", "=", bank_account.id),
                    ("should_qr_parsing", "=", True),
                ],
                limit=1,
            )
        elif journal and journal.should_qr_parsing:
            journal = journal_obj.search(
                [
                    ("type", "=", "bank"),
                    ("bank_account_id", "=", journal.bank_account_id.id),
                    ("should_qr_parsing", "=", False),
                ],
                limit=1,
            )
        return journal
