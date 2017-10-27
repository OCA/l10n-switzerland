# -*- coding: utf-8 -*-
# Copyright 2017 Jean Respen and Nicolas Bessi
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{'name': 'Payment slip alternate layout(s)',
 'version': '10.0.1.0.0',
 'author': 'Camptocamp, Odoo Community Association (OCA)',
 'maintainer': 'Camptocamp, Odoo Community Association (OCA)',
 'summary': """Add new BVR/ESR payment slip layouts like invoice
     with slip on same document""",
 'category': 'Accounting',
 'complexity': 'normal',
 'depends': ['base', 'account', 'l10n_ch_payment_slip'],
 'website': 'http://www.camptocamp.com',
 'data': [
     'report/report.xml',
     'view/company_view.xml',
     'view/account_invoice.xml'
 ],
 'demo': [],
 'test': [],
 'installable': True,
 'auto_install': False,
 'license': 'AGPL-3',
 'application': False,
 }
