# -*- coding: utf-8 -*-
# Copyright 2009 Camptocamp SA
# Copyright 2015 Agile Business Group
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{'name': 'Switzerland - Bank Payment File (DTA)',
 'summary': 'Electronic payment file for Swiss bank (DTA)',
 'version': '10.0.1.0.1',
 'author': "Camptocamp,Odoo Community Association (OCA)",
 'category': 'Localization',
 'website': 'http://www.camptocamp.com',
 'license': 'AGPL-3',
 'depends': ['base', 'l10n_ch_base_bank',
             'account_payment_order',
             'document'],
 'data': ['data/account_payment_method.xml',
          ],
 'demo': ["demo/dta_demo.xml"],
 'auto_install': False,
 'installable': True,
 'post_init_hook': 'update_bank_journals',
 'images': []
 }
