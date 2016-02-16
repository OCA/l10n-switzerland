# b-*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2015 brain-tec AG (http://www.braintec-group.com)
#    All Right Reserved
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

{'name': 'Switzerland - Payment Register',
 'summary': 'Allow to register payments from invoices',
 'description': """

===================================

This addons allows you to generate .

""",
 'version': '9.0.1.0.1',
 'author': "",
 'category': 'Localization',
 'website': '',
 'license': 'AGPL-3',
 'depends': ['base', 'l10n_ch_base_bank', 'document'],
 'data': ["wizard/payment_order_create_view.xml",
          "views/payment_register_view.xml",
          "views/payment_register_line_view.xml",
          ],
 # 'demo': ["demo/dta_demo.xml"],
 # 'test': ["test/l10n_ch_dta.yml"],
 'auto_install': False,
 'installable': True,
 'images': []
 }
