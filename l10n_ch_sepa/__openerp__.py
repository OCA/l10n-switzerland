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
    "name": "Switzerland - SEPA Electronic Payment File",
    "summary": "Generate pain.001 Credit Transfert Files for your payments",
    "version": "7.0.1.1",
    "category": "Finance",
    "author": "Camptocamp,Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": [
        "account",
        "l10n_ch",
        "l10n_ch_base_bank",
        "base_iban",
        "account_payment",
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
