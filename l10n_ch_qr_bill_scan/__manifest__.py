# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Switzerland - QR-bill scan",
    "summary": "Scan QR-bill to create vendor bills",
    "version": "14.0.1.0.0",
    "author": "Camptocamp,Odoo Community Association (OCA)",
    "category": "Localization",
    "website": "https://github.com/OCA/l10n-switzerland",
    "license": "AGPL-3",
    "depends": ["l10n_ch", "account_invoice_import"],
    "data": ["wizard/account_invoice_import_view.xml"],
    "auto_install": False,
    "installable": True,
}
