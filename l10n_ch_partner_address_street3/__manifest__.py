# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Switzerland - Take into account street3 in QR-bills",
    "summary": "Take into account street3 in QR-bills",
    "version": "16.0.1.0.0",
    "author": "Camptocamp,Odoo Community Association (OCA)",
    "category": "Localization",
    "website": "https://github.com/OCA/l10n-switzerland",
    "license": "AGPL-3",
    "depends": [
        "l10n_ch",
        "partner_address_street3",
    ],
    "data": ["report/swissqr_report.xml"],
    "auto_install": True,
}
