# -*- coding: utf-8 -*-
# Copyright 2016 Open Net Sàrl
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Accounting Import WinBIZ',
    'version': '9.0.1.0.1',
    'category': 'Localization',
    'website': 'https://opennet.ch',
    'author': 'Open Net Sàrl, Camptocamp, Odoo Community Association (OCA)',
    'license': 'AGPL-3',
    'depends': [
        'account_accountant',
    ],
    'external_dependencies': {
        'python': ['xlrd'],
    },
    'data': [
        'security/security.xml',
        'wizard/l10n_ch_import_winbiz_view.xml',
        'views/account_journal_view.xml',
        'views/menu.xml',
    ],
    'application': False,
    'installable': True,
}
