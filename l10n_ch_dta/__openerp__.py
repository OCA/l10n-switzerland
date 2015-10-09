# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi. Copyright Camptocamp SA
#    Ported to v8.0 by Agile Business Group <http://www.agilebg.com>
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

{'name': 'Switzerland - Bank Payment File (DTA)',
 'summary': 'Electronic payment file for Swiss bank (DTA)',
 'description': """
Swiss bank electronic payment (DTA)
===================================

This addons allows you to generate an electronic payment file for Swiss bank
(known as DTA). You'll found the wizard in payment order.

""",
 'version': '8.0.1.0.1',
 'author': "Camptocamp,Odoo Community Association (OCA)",
 'category': 'Localization',
 'website': 'http://www.camptocamp.com',
 'license': 'AGPL-3',
 'depends': ['base', 'account_payment', 'l10n_ch_base_bank', 'document'],
 'data': ["wizard/create_dta_view.xml",
          "bank_view.xml"],
 'demo': ["demo/dta_demo.xml"],
 'test': ["test/l10n_ch_dta.yml"],
 'auto_install': False,
 'installable': True,
 'images': []
 }
