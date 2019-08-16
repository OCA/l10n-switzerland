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
 'version': '8.0.3.0.0',
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
