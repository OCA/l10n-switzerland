# Copyright 2024 Camptocamp (<https://www.camptocamp.com>).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "L10n Switzerland - QR Bill without Amount",
    "version": "16.0.1.0.0",
    "category": "Localization",
    "summary": "Print QR Bill without amount",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-switzerland",
    "license": "AGPL-3",
    "depends": [
        "l10n_ch",
        "account_payment_partner",
    ],
    "data": [
        "views/payment_mode.xml",
        "report/swissqr_report.xml",
    ],
    "installable": True,
    "auto_install": False,
}
