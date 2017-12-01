# Copyright 2012-2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{'name': 'Switzerland - ISR inpayment slip (PVR/BVR/ESR)',
 'summary': 'Print inpayment slip from your invoices',
 'version': '11.0.1.0.0',
 'author': "Camptocamp,Odoo Community Association (OCA)",
 'category': 'Localization',
 'website': 'http://www.camptocamp.com',
 'license': 'AGPL-3',
 'depends': [
     'account_invoicing',
     'l10n_ch_base_bank',
     'base_transaction_id',  # OCA/bank-statement-reconcile
 ],
 'data': [
     "views/company.xml",
     "views/bank.xml",
     "views/account_invoice.xml",
     "wizard/isr_batch_print.xml",
     "wizard/isr_import_view.xml",
     "report/report_declaration.xml",
     "security/ir.model.access.csv"
 ],
 'demo': [],
 'auto_install': False,
 'installable': True,
 'images': []
 }
