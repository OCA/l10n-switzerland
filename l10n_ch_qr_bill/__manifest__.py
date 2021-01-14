# -*- coding: utf-8 -*-
# Copyright 2019-2020 Odoo
# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Switzerland - QR-bill',
    'summary': 'Print QR-bill for your invoices [Backport from Odoo l10n_ch]',
    'version': '10.0.1.2.0',
    'author': "Camptocamp,Odoo Community Association (OCA)",
    'category': 'Localization',
    'website': 'https://github.com/OCA/l10n-switzerland',
    'license': 'LGPL-3',
    'depends': ['report', 'account', 'base_iban'],
    'data': [
        'data/paperformat.xml',
        'views/account_invoice_view.xml',
        'views/res_bank.xml',
        'report/swissqr_report.xml',
    ],
    'auto_install': False,
    'installable': True,
}
