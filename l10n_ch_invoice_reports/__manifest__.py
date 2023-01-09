# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Switzerland - Invoice Reports with payment option",
    "summary": "Extend invoice to add ISR/QR payment slip",
    "version": "15.0.1.0.0",
    "author": "Camptocamp,Odoo Community Association (OCA)",
    "category": "Localization",
    "website": "https://github.com/OCA/l10n-switzerland",
    "license": "AGPL-3",
    "depends": ["account", "l10n_ch", "web"],
    "data": ["data/reports.xml", "views/res_config_settings.xml"],
    "auto_install": False,
    "installable": True,
}
