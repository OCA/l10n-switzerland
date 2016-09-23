# -*- coding: utf-8 -*-
# Copyright 2015 Camptocamp SA
# Copyright 2016 Open Net Sàrl
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Accounting Import Cresus',
    'summary': 'Allows to import Crésus .txt files containing journal entries '
               'into Odoo.',
    'version': '9.0.1.0.0',
    'category': 'accounting',
    'website': 'https://odoo-community.org/',
    'author': 'Camptocamp, Open Net Sàrl, Odoo Community Association (OCA)',
    'license': 'AGPL-3',
    'application': False,
    'installable': True,
    'depends': [
        'account_accountant',
    ],
    'data': [
        'wizard/l10n_ch_import_cresus_view.xml',
        'views/account_tax_view.xml',
        'views/menu.xml',
    ],
}
