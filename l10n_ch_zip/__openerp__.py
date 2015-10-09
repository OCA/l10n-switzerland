# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi, Olivier Jossen, Guewen Baconnier
#    Copyright 2011-2014 Camptocamp SA
#    Copyright 2014 brain-tec AG
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
    'name': 'Switzerland - Postal codes (ZIP) list',
    'version': '8.0.2.0.0',
    'author': '''
        Camptocamp,
        brain-tec AG,
        copadoMEDIA UG,
        Odoo Community Association (OCA)
    ''',
    'category': 'Localisation',
    'website': 'http://www.camptocamp.com',
    'license': 'AGPL-3',
    'summary': 'Provides all Swiss postal codes for auto-completion',
    'depends': [
        'base',
        'base_location',  # in https://github.com/OCA/partner-contact/
        'l10n_ch_states',  # in https://github.com/OCA/l10n-switzerland/
    ],
    'data': ['l10n_ch_better_zip.xml'],
    'images': [],
    'demo': [],
    'auto_install': False,
    'installable': True,
    'application': True,
}
