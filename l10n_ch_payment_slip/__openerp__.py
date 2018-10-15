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

This addon allows you to print the ESR/BVR report Using Qweb report.

The ESR/BVR is grenerated as an image and is availabe in a fields
of the `l10n_ch.payment_slip` Model.

The ESR/BVR is created each time an invoice is validated.
To modify it you have to cancel it and reconfirm the invoice.

You can adjust the print out of ESR/BVR, which depend on each printer,
for every company in the "BVR Data" tab.

This is especialy useful when using pre-printed paper.
An option also allow you to print the ESR/BVR in background when using
white paper.

This module will also allows you to import v11 files provided
by financial institute into a bank statement

To do so, use the wizard provided in bank statement.

This module also adds transaction_ref field on entries in order to manage
reconciliation in multi payment context (unique reference needed on
account.move.line). Many BVR can now be printed from on invoice for each
payment terms.


""",
 'version': '8.0.2.1.1',
 'author': "Camptocamp,Odoo Community Association (OCA)",
 'category': 'Localization',
 'website': 'http://www.camptocamp.com',
 'license': 'AGPL-3',
 'depends': ['base',
             'account',
             'account_payment',
             'report',
             'l10n_ch_base_bank',
             'base_transaction_id'],
 'data': ["company_view.xml",
          "bank_view.xml",
          "account_invoice_view.xml",
          "wizard/bvr_import_view.xml",
          "report/report_declaration.xml",
          "security/ir.model.access.csv"],
 'demo': [],
 'test': [],
 'auto_install': False,
 'installable': True,
 'images': []
 }
