# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi. Copyright Camptocamp SA
#    Financial contributors: Hasa SA, Open Net SA,
#                            Prisme Solutions Informatique SA, Quod SA
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

{'name': 'Switzerland - Payment Slip (BVR/ESR)',
 'summary': 'Print ESR/BVR payment slip with your invoices',
 'description': """
Swiss Payment slip known as ESR/BVR
===================================

This addon allows you to print the ESR/BVR report. As the reports are made
with webkit report system, you'll need the wkhtmltopdf lirary installed on
your system (http://wkhtmltopdf.org/).

Be sure to have the proper version (32 or 64 bit) installed and in
your system path or define the path in

    "Settings -> Technical -> Parameters -> System Parameters -> webkit_path".

You can adjust the print out of ESR/BVR, which depend on each printer,
for every company in the "BVR Data" tab.
This is especialy useful when using pre-printed paper.
An option also allow you to print the ESR/BVR in background when using
white paper.

This module will also allows you to reconcile from V11 files provided
by financial institutes.

To do so, use the wizard provided in bank statement.

If voucher is installed importing V11 files will generate a voucher
if possible in statement lines.

This module also adds transaction_ref field on entries in order to manage
reconciliation in multi payment context (unique reference needed on
account.move.line). Many BVR can now be printed from on invoice for each
payment terms.

In the future, this field may be removed from this addon
but will remain in the data model via new banking addons dependence.

""",
 'version': '1.2',
 'author': 'Camptocamp',
 'category': 'Localization',
 'website': 'http://www.camptocamp.com',
 'depends': ['base', 'report_webkit', 'l10n_ch_base_bank'],
 'data': ["company_view.xml",
          "bank_view.xml",
          "account_invoice_view.xml",
          "report/multi_report_webkit_html_view.xml",
          "wizard/bvr_import_view.xml",
          "data.xml"],
 'demo': [],
 'test': [],  # To be ported or migrate to unit tests or scenarios
 'auto_install': False,
 'installable': True,
 'images': []
 }
