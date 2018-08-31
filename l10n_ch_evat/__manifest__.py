# -*- coding: utf-8 -*-
# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Switzerland - E-VAT Declaration",
    "summary": "Module summary",
    "version": "10.0.1.0.0",
    "category": "accounting",
    "website": "https://github.com/OCA/l10n-switzerland",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "installable": True,
    "depends": [
        "l10n_ch",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/evat_xml_report.xml",
    ],
}
