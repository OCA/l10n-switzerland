# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Guewen Baconnier
#    Copyright 2014 Camptocamp SA
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

{'name': 'Switzerland - Bank Payment File (DTA) Transaction ID Compatibility',
 'version': '8.0.1.0.0',
 'author': "Camptocamp,Odoo Community Association (OCA)",
 'maintainer': 'Camptocamp',
 'license': 'AGPL-3',
 'category': 'Hidden',
 'depends': ['l10n_ch_dta',
             'base_transaction_id'],
 'description': """
Swiss bank electronic payment (DTA) - Transaction ID Compatibility
==================================================================

Link module between the Swiss Payment File (DTA) module
(l10n_ch_dta) and the module adding a transaction ID
field (base_transaction_id).

When an invoice has a transaction ID, the DTA is exported with this ID
as reference. This is used by the bank-statement-reconcile project
in the banking addons (https://launchpad.net/banking-addons).

""",
 'website': 'http://www.camptocamp.com',
 'data': [],
 'tests': [],
 'installable': True,
 'auto_install': True,
 }
