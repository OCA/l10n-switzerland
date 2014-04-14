# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Guewen Baconnier
#    Copyright 2014 Camptocamp SA
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

{'name' : 'Swiss Localization BVR/ESR - Bank statement Completion',
 'version' : '1.0',
 'author' : 'Camptocamp',
 'maintainer': 'Camptocamp',
 'license': 'AGPL-3',
 'category': 'Hidden',
 'depends' : ['l10n_ch_payment_slip',
              'account_statement_base_completion',  # lp:banking-addons/bank-statement-reconcile-7.0 
              ],
 'description': """
Swiss Localization BVR/ESR - Bank statement Completion
======================================================

Link module between the Swiss localization BVR/ESR module
(l10n_ch_payment_slip) and the module adding a transaction ID
field in the bank statement (account_statement_base_completion).

It adds a completion rule to search the partner from the invoice
using the BVR/ESR reference.

When importing a BVR/ESR, the transaction ID is also copied to the
transaction id field of the bank statement.

 """,
 'website': 'http://www.camptocamp.com',
 'data': ['data.xml',
          ],
 'tests': [],
 'installable': True,
 'auto_install': True,
}
