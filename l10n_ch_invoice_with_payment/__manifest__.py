# Copyright 2012-2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Switzerland - Invoice with payment option",
    "summary": "Extend invoice to add ISR/QR payment slip",
    "version": "13.0.1.0.0",
    "author": "Camptocamp,Odoo Community Association (OCA)",
    "category": "Localization",
    "website": "https://github.com/OCA/l10n-switzerland",
    "license": "AGPL-3",
    "depends": ["account", "l10n_ch"],
    "data": [
        "data/data.xml",
        "templates/account.xml",
    ],
    "auto_install": False,
    "installable": True,
}
