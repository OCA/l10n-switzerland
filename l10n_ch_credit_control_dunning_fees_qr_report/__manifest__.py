# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Swiss Credit Control QR report",
    "version": "16.0.1.0.0",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "category": "Finance",
    "website": "https://github.com/OCA/l10n-switzerland",
    "depends": [
        "account_credit_control",
        "account_credit_control_dunning_fees",
        "l10n_ch",
    ],
    "data": [
        "reports/swissqr_report.xml",
        "reports/credit_control_summary_report.xml",
    ],
}
