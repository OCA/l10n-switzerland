# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi. Copyright Camptocamp SA
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

{'name': 'Switzerland - Bank type',
 'summary': 'Types and number validation for swiss electronic pmnt. DTA, ESR',
 'description': """
Swiss bank type and fields
==========================

This addons will add different bank types required by specific swiss electronic
payment like DTA and ESR. It allows to manage both Post and Bank systems.

It'll perform some validation when entring bank account number or ESR number
in invoice and add some Swiss specific fields on bank.

This module is required if you want to use electornic payment in Switzerland.
""",
 'version': '1.2',
 'author': "Camptocamp,Odoo Community Association (OCA)",
 'category': 'Localization',
 'website': 'http://www.camptocamp.com',
 'license': 'AGPL-3',
 'depends': ['account'],
 'data': ['bank_view.xml', 'bank_data.xml'],
 'demo': [],
 'test': [],
 'auto_install': False,
 'installable': True,
 'images': []
 }
