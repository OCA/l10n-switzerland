# -*- coding: utf-8 -*-
#
#  File: __openerp__.py
#  Module: l10n_ch_scan_bvr
#
##############################################################################
#
#    Author: Nicolas Bessi, Vincent Renaville
#    Copyright 2012 Camptocamp SA
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


{
    'name': 'Switzerland - Scan ESR/BVR to create invoices',
    'category': 'Generic Modules/Others',
    'author': "Camptocamp, Odoo Community Association (OCA), Open-Net",
    'depends': ['l10n_ch'],
    'version': '1.8',
    'demo': [],
    'website': 'http://camptocamp.com',
    'license': 'AGPL-3',
    'data': [
        'views/partner_view.xml',
        'wizard/scan_bvr_view.xml',
    ],
    'auto_install': False,
    'installable': True
}
