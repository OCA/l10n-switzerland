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

{"name": "Switzerland - Bank list",
 "summary": "Banks names, addresses and BIC codes",
 "description": """
Swiss bank list
===============
This module will load all Swiss banks in OpenERP with their name,
address and BIC code to ease the input of bank account.

It is not mandatory to use OpenERP in Switzerland,
but can improve the user experience.

 """,
    "version": "7.0",
    "author": "Camptocamp",
    "category": "Localisation",
    "website": "http://www.camptocamp.com",
    "depends": ["l10n_ch"],
    "data": ["bank.xml"],
    "update_xml": [],
    "active": True,
    'installable': False,
 }
