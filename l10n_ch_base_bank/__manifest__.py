# -*- coding: utf-8 -*-
# © 2012 Nicolas Bessi (Camptocamp SA)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{'name': 'Switzerland - Bank type',
 'summary': 'Types and number validation for swiss electronic pmnt. DTA, ESR',
 'version': '10.0.1.0.0',
 'author': "Camptocamp,Odoo Community Association (OCA)",
 'category': 'Localization',
 'website': 'http://www.camptocamp.com',
 'license': 'AGPL-3',
 'depends': ['account_payment_partner', 'base_iban'],
 'data': [
     'views/bank.xml',
     'views/invoice.xml',
 ],
 'demo': [],
 'test': [],
 'auto_install': False,
 'installable': True,
 'images': []
 }
