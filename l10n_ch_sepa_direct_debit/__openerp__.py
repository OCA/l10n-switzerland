# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Anar Baghirli
#    Copyright 2017 Camptocamp SA
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
    "name": "Switzerland - SEPA Direct Debit Electronic Payment File",
    "summary": "Generate pain.008 Direct Debit Files for your payments",
    "version": "7.0.1.0.0",
    "category": "Finance",
    "description": """
Swiss electronic payment (SEPA)
===============================

This addons allows you to generate SEPA electronic payment file for
Switzerland.
You'll found the wizard in payment order.

This module designed for Swiss payment is also generic for euro payments
as the Swiss standards are slightly different.
It intends to be reusable to accept new definition of specific standards
by country.

It currently supports the "pain.008" norm for Direct Debit Initiation.

""",
    "author": "Camptocamp,Odoo Community Association (OCA)",
    "depends": [
        "account",
        "l10n_ch_base_bank",
        "base_iban",
        "account_payment",
        "account_banking_sepa_direct_debit",
    ],
    "data": [
        "data/payment_type_sepa_sct.xml",
    ],
    "installable": True,
    "active": True,
}
