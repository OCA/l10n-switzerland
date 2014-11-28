# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi, Olivier Jossen, Guewen Baconnier
#    Copyright Camptocamp SA
#    Copyright brain-tec AG
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
    'name': 'Switzerland - Bank list',
    'version': '8.0',
    'author': 'Camptocamp, brain-tec AG',
    'category': 'Localisation',
    'website': 'http://www.camptocamp.com',
    'summary': 'Banks names, addresses and BIC codes',
    'description': """
Swiss bank list
===============
This module will load all Swiss banks in OpenERP with their name,
address and BIC code to ease the input of bank account.

It is not mandatory to use OpenERP in Switzerland,
but can improve the user experience.

IMPORTANT:
The module contains the newest bank data (21.10.2014).
If you want to update all your banks, update via link 'Update Banks' in section 'Bank & Cash' under 'Settings/Configuration/Accounting'.

""",
    'depends': ['l10n_ch', 'l10n_ch_base_bank'],
    'data': [
              'bank.xml',
              'res_config_view.xml'
    ],
    'images': [],
    'demo': [],
    'auto_install': False,
    'installable': True,
    'application': True,
}
