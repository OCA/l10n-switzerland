# Copyright 2026 Camptocamp SA (https://www.camptocamp.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Invoice YellowBill Export",
    "summary": "Generate the eBill YellowBill (ybInvoice) XML for an invoice",
    "version": "19.0.1.0.0",
    "license": "AGPL-3",
    "author": "Camptocamp,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-switzerland",
    "depends": [
        "account",
        "l10n_ch",
        "sale",
    ],
    "data": [
        "templates/invoice_yellowbill.xml",
    ],
}
