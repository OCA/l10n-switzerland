# -*- coding: utf-8 -*-
# Copyright 2014-2017 Compassion CH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{'name': "Swiss bank statements import",
 'version': '9.0.1.0.1',
 'author': "Compassion CH, Camptocamp, Odoo Community Association (OCA)",
 'category': 'Finance',
 'complexity': 'normal',
 'depends': [
     'account_bank_statement_import_camt',
 ],
 'external_dependencies': {
     'python': ['xlrd', 'wand'],
 },
 'website': 'http://www.compassion.ch/',
 'data': [
     'views/statement_line_view.xml',
     'views/l10n_ch_account_statement_base_import.xml',
     'views/account_bank_statement_import_postfinance_view.xml',
     ],
 'qweb': ['static/src/xml/l10n_ch_statement_line_layout.xml'],
 'test': [],
 'installable': True,
 'images': [],
 'auto_install': False,
 'license': 'AGPL-3'}
