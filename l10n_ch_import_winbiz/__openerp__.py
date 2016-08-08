# -*- coding: utf-8 -*-
# Copyright 2015 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Accounting Import WinBIZ',
    'version': '9.0.1.0.0',
    'depends': [
        'account_accountant',
    ],
    'external_dependencies': {
        'python': ['xlrd'],
    },
    'author': 'Camptocamp, Open Net Sàrl, Odoo Community Association (OCA)',
    'website': 'http://odoo-community.org',
    'license': 'AGPL-3',
    'data': [
        'security/security.xml',
        'wizard/l10n_ch_import_winbiz_view.xml',
        'views/account_journal_view.xml',
        'views/menu.xml',
    ],
    'application': False,
    'installable': True,
}
