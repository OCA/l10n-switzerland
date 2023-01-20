# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)


{
    "name": "Switzerland - CHF Cash Rounding",
    "summary": "Apply cash rounding for CHF currency",
    "version": "15.0.1.0.0",
    "author": "Camptocamp,Odoo Community Association (OCA)",
    "category": "Localization",
    "website": "https://github.com/OCA/l10n-switzerland",
    "license": "AGPL-3",
    "depends": ["account", "l10n_ch"],
    "data": [
        "data/cash_rounding.xml",
    ],
    "auto_install": False,
    "installable": True,
}
