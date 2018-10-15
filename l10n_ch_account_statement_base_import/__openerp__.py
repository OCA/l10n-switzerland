# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Emanuel Cino
#    Copyright 2014 Compassion CH
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{'name': "Swiss bank statements import",
 'version': '8.0.1.0.1',
 'author': "Compassion CH, Camptocamp, Odoo Community Association (OCA)",
 'category': 'Finance',
 'complexity': 'normal',
 'depends': [
     'account',
     'account_bank_statement_import_camt',
 ],
 'external_dependencies': {
     'python': ['xlrd', 'wand'],
 },
 'website': 'http://www.compassion.ch/',
 'data': [
     'views/statement_line_view.xml',
     'views/l10n_ch_account_statement_base_import.xml'
     ],
 'qweb': ['static/src/xml/l10n_ch_statement_line_layout.xml'],
 'test': [],
 'installable': True,
 'images': [],
 'auto_install': False,
 'license': 'AGPL-3'}
