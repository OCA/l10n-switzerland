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
    "name": "Switzerland - SEPA Payment File",
    "version": "6.1",
    "category": "Finance",
    "description": """
Swiss electronic payment (SEPA)
===============================

This addons allows you to generate SEPA electronic payment file for Switzerland.
You'll found the wizard in payment order.

This module designed for Swiss payment is also generic for euro payments
as the Swiss standards are slightly different.
It intends to be reusable to accept new definition of specific standards
by country.  

It currently supports the "pain.001$2 norm for Credit Transfert Initiation.
       
""",
    "author": "Camptocamp",
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
    "installable": False,
    "active": False,
#    'certificate': 'certificate',
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: