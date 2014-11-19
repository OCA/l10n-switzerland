# b-*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2014 brain-tec AG (http://www.brain-tec.ch)
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
{
    'name': 'Switzerland - Postal codes (ZIP) list',
    'version': '2.0.1',
    'author': 'brain-tec AG',
    'category': 'Localisation',
    'website': 'http://www.brain-tec.ch',
    'summary': 'Provides all Swiss postal codes for auto-completion',
    'description': """
Swiss postal code (ZIP) list
============================

This module will load all Swiss postal codes (ZIP) in Odoo to
ease the input of partners.

It is not mandatory to use Odoo in Switzerland,
but can improve the user experience.

""",
    'depends': ['base', 'base_location'],
    'init_xml': ['data/set_old_res_better_zip_entries_inactive.sql'],
    'data': ['l10n_ch_better_zip.xml'],
    'images': [],
    'demo': [],
    'auto_install': False,
    'installable': True,
    'application': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
