# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright 2014 Agile Business Group <http://www.agilebg.com>
#    Author: Lorenzo Battistini <lorenzo.battistini@agilebg.com>
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

{'name': 'Switzerland - Import BVR/ESR into vouchers',
 'summary': 'Import Payment Slip (BVR/ESR) into vouchers',
 'description': """
This module allows you to import v11 files provided
by financial institute into a payment voucher

To do so, use the wizard provided under Accounting -> Customers.
""",
 'version': '8.0.1.0.0',
 'author': 'Agile Business Group',
 'category': 'Localization',
 'website': 'http://www.agilebg.com',
 'depends': ['l10n_ch_payment_slip'],
 'data': [
     "wizard/bvr_import_view.xml",
     ],
 'demo': [],
 'test': [],
 'auto_install': False,
 'installable': True,
 'images': []
 }
