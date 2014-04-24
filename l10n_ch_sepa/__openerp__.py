# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Yannick Vaucher
#    Copyright 2011 Camptocamp SA
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
    "name": "SEPA",
    "version": "1.0",
    "category": "Finance",
    "description": """
SEPA payments
=============

pain.001 for Credit Transfert Initiation

This module designed for Swiss payment is based on the norm for euro payments
but implements the special Swiss extensions.
It intends to be reusable to accept new definition of specific standards
by country.

TODO: Needs to be fully tested with a FI

    """,
    "author": "Camptocamp",
    "depends": [
        "account",
        "l10n_ch"
    ],
    "data": [
        "wizard/wiz_pain_001_view.xml",
    ],
    "test": [
        "test/pain001_eu.yml",
        "test/pain001_ch.yml",
    ],
    "installable": True,
    "active": True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
