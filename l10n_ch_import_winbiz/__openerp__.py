# -*- coding: utf-8 -*-
# Copyright 2015 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Account Import Winbiz',
    'version': '1.0',
    'depends': [
        'account',
    ],
    'author': 'Camptocamp, Odoo Community Association (OCA)',
    'website': 'http://www.camptocamp.com',
    'license': 'AGPL-3',
    'data': [
        'security/security.xml',
        'wizard/l10n_ch_import_winbiz_view.xml',
        'views/account_tax_view.xml',
        'views/menu.xml',
    ],
    'installable': True,
}
