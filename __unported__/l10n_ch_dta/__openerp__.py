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

{'name': 'Switzerland - Bank Payment File (DTA)',
 'description':  """
Swiss localization supplier bank payment file known as DTA file :
=================================================
Generate a DTA file for swiss banking system from payment order

""",
 'version': '1.0.1',
 'author': 'Camptocamp',
 'category': 'Localization',
 'website': 'http://www.camptocamp.com',
 'depends': ['base', 'account_payment', 'l10n_ch_base_bank', 'document'],
 'data': ["wizard/create_dta_view.xml",
          "bank_view.xml"],
 'demo': ["demo/dta_demo.xml"],
 'test': [], # To be ported or migrate to unit tests or scenarios
 'auto_install': False,
 'installable': True,
 'images': []
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
