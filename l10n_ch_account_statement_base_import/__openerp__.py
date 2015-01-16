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
 'version': '0.3',
 'author': 'Compassion CH',
 'category': 'Finance',
 'complexity': 'normal',
 'depends': [
     'account_statement_base_import',
 ],
 'external_dependencies': {
     'python': ['xlrd'],
 },
 'description': """
 This module adds several import types to the module
 account_statement_base_import, in order to read swiss bank statements.
 It currently supports the following file formats :

 * .v11, .esr, .bvr formats (ESR standard) for records of type 3
   (type 4 is ready to be implemented)
 * .g11 format from Postfinance S.A. for Direct Debit records of type 2
 * XML format from Postfinance S.A.
 * .csv format from Raiffeisen Bank
 * .csv format from UBS Bank [CH-FR]

 Warning : this module requires the python library 'xlrd'.
 """,
 'website': 'http://www.compassion.ch/',
 'data': ['view/statement_view.xml'],
 'test': [],
 'installable': True,
 'images': [],
 'auto_install': False,
 'license': 'AGPL-3',
 }
