# -*- encoding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi. Copyright Camptocamp SA
#    Donors: Hasa SA, Open Net SA and Prisme Solutions Informatique SA
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

{'name': 'Switzerland - Payment Slip',
 'description':  """
Swiss localization Payment slip Known as ESR/BVR:
=================================================
This addon allows you to print the ESR/BVR report.
It will also allows you to reconcile from V11 filea provided by financial
institutes.
""",
 'version': '1.0',
 'author': 'Camptocamp',
 'category': 'Localization',
 'website': 'http://www.camptocamp.com',
 'depends': ['l10n_ch', 'report_webkit', "l10n_ch_base_bank",
             "base_header_webkit", "invoice_webkit"],
 'data': ['sterchi_chart/account.xml',
          'sterchi_chart/vat2011.xml',
          'sterchi_chart/fiscal_position.xml' ],
 'demo': [],
 'test': [],
 'auto_install': False,
 'installable': True,
 'images': []
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
