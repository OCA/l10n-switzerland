# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2011 Camptocamp SA (http://www.camptocamp.com)
# All Right Reserved
#
# Author : Yannick Vaucher (Camptocamp)
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    "name": "SEPA",
    "version": "6.1",
    "category": "Finance",
    "description": """
        SEPA payments
        
        pain.001 for Credit Transfert Initiation
        
        This module designed for Swiss payment is also generic for euro payments
        as the Swiss standards are slightly different.
        It intends to be reusable to accept new definition of specific standards
        by country.  
        
        TODO: Needs to be fully tested with a FI
        
        WARNING: This module has been developed in 6.0 and has never been launched in 6.1 yet
        
    """,
    "author": "Camptocamp,Odoo Community Association (OCA)",
    "depends": [
            "base",
            "account",
            "l10n_ch"
    ],
    "init_xml": [],
    "update_xml": [
            "wizard/wiz_pain_001_view.xml",
    ],
    "test" : [
            "test/pain001_eu.yml",
            "test/pain001_ch.yml",
    ],
    "demo_xml": [],
    "installable": True,
    "active": False,
#    'certificate': 'certificate',
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: