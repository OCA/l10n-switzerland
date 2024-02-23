# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Switzerland - Account credit control invoices",
    "summary": "Extend account credit control to print credit control summary with invoices",
    "version": "14.0.1.0.0",
    "author": "Camptocamp,Odoo Community Association (OCA)",
    "category": "Localization",
    "website": "https://github.com/OCA/l10n-switzerland",
    "license": "AGPL-3",
    "depends": [
        "account_credit_control",
        "l10n_ch_invoice_reports",
    ],
    "data": [
        "views/res_config_settings.xml",
    ],
    "auto_install": False,
    "installable": True,
}
