# -*- coding: utf-8 -*-
# © 2012-2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{'name': 'Switzerland - Payment Slip (BVR/ESR)',
 'summary': 'Print ESR/BVR payment slip with your invoices',
 'version': '9.0.2.2.1',
 'author': "Camptocamp,Odoo Community Association (OCA)",
 'category': 'Localization',
 'website': 'http://www.camptocamp.com',
 'license': 'AGPL-3',
 'depends': [
     'base',
     'account',
     'report',
     'l10n_ch_base_bank',
     'base_transaction_id',  # OCA/bank-statement-reconcile
 ],
 'data': [
     "views/company.xml",
     "views/bank.xml",
     "views/account_invoice.xml",
     "wizard/bvr_import_view.xml",
     "report/report_declaration.xml",
     "security/ir.model.access.csv"
 ],
 'demo': [],
 'test': [],
 'auto_install': False,
 'installable': True,
 'images': []
 }
