# Copyright 2012-2017 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{'name': 'Switzerland - Bank type',
 'summary': 'Types and number validation for swiss electronic pmnt. DTA, ESR',
 'version': '11.0.1.2.0',
 'author': "Camptocamp,Odoo Community Association (OCA)",
 'category': 'Localization',
 'website': 'http://www.camptocamp.com',
 'license': 'AGPL-3',
 'depends': ['account_payment_partner', 'base_iban'],
 'data': [
     'security/security.xml',
     'views/bank.xml',
     'views/invoice.xml',
 ],
 'demo': [],
 'test': [],
 'auto_install': False,
 'installable': True,
 'images': []
 }
