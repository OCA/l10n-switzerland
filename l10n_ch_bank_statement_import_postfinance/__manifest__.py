# -*- coding: utf-8 -*-
# Copyright 2015 Nicolas Bessi Camptocamp SA
# Copyright 2017-2019 Compassion CH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{'name': "Swiss bank statements import",
 'version': '11.0.0.0.0',
 'author': "Compassion CH, Camptocamp, Odoo Community Association (OCA)",
 'category': 'Finance',
 'complexity': 'normal',
 'depends': [
     'account_bank_statement_import_camt_oca',
 ],
 'external_dependencies': {
     'python': ['xlrd'],
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
