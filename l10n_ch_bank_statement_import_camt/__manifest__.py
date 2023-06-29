# Copyright 2023 Compassion CH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "l10n_ch_bank_statement_import_camt",
    "version": "14.0.1.0.0",
    "category": "Account",
    "website": "https://github.com/OCA/l10n-switzerland",
    "author": "Compassion CH, " "Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "installable": True,
    "data": ["views/account_journal_view.xml"],
    "depends": ["account_statement_import_camt54", "l10n_ch_qriban"],
}
