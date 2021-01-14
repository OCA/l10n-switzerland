# Copyright 2012-2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{'name': 'Switzerland - ISR inpayment slip (PVR/BVR/ESR)',
 'summary': 'Print inpayment slip from your invoices',
 'version': '12.0.3.3.0',
 'author': "Camptocamp,Odoo Community Association (OCA)",
 'category': 'Localization',
 'website': 'https://github.com/OCA/l10n-switzerland',
 'license': 'AGPL-3',
 'depends': [
     'account',
     'l10n_ch_base_bank',
     'web',
     'l10n_ch',
 ],
 'data': [
     "views/assets.xml",
     "views/bank.xml",
     "views/account_invoice.xml",
     "views/res_config_settings_views.xml",
     "wizard/isr_batch_print.xml",
     "report/report_declaration.xml",
     "security/ir.model.access.csv"
 ],
 'auto_install': False,
 'installable': True,
 'external_dependencies': {
     'python': [
         'PyPDF2',
     ]
 }
 }
