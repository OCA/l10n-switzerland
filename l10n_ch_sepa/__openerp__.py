# -*- coding: utf-8 -*-
# © 2016 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# © 2011 Camptocamp SA (Yannick Vaucher)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Switzerland - ISO 20022 payment file",
    "summary": "Generate ISO 20022 credit transfert and direct debit files",
    "version": "9.0.1.0.0",
    "category": "Finance",
    "author": "Akretion,Camptocamp,Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": [
        "account_banking_pain_base",
        "l10n_ch_base_bank",
    ],
    "data": [
        'views/account_payment_line.xml',
        'views/bank_payment_line.xml',
        ],
    "test": [
        # "test/pain001_ch.yml",
    ],
    'installable': True,
}
