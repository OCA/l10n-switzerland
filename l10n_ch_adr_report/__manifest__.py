# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
{
    "name": "ADR Products Swiss Report",
    "summary": "Print Delivery report to ADR swiss configuration",
    "version": "14.0.1.0.0",
    "category": "Product",
    "website": "https://github.com/OCA/l10n-switzerland",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": ["l10n_eu_product_adr_dangerous_goods", "stock", "delivery"],
    "data": [
        "report/DG_ch_delivery_report.xml",
        "views/assets.xml",
    ],
}
