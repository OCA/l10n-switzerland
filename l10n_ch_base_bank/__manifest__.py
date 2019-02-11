# Copyright 2012-2019 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{'name': 'Switzerland - Bank type',
 'summary': 'Types and number validation for swiss electronic pmnt. DTA, ESR',
 'version': '12.0.1.0.0',
 'author': "Camptocamp,Odoo Community Association (OCA)",
 'category': 'Localization',
 'website': 'https://github.com/OCA/l10n-switzerland',
 'license': 'AGPL-3',
 'depends': [
     'account_payment_order',
     'account_payment_partner',
     'base_iban'],
 'data': [
     'views/bank.xml',
     'views/invoice.xml',
 ],
 'auto_install': False,
 'installable': True,
 }
