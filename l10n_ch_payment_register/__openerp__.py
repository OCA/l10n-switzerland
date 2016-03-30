# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2015 brain-tec AG (http://www.braintec-group.com)
#    All Right Reserved
#
#    License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
##############################################################################

{'name': 'Switzerland - Payment Register',
 'summary': 'Allow to register payments from invoices',
 'version': '9.0.1.0.1',
 'author': "Odoo Community Association (OCA), "
            "Brain-tec AG",
 'category': 'Localization',
 'website': '',
 'license': 'AGPL-3',
 'depends': ['base', 'l10n_ch_base_bank', 'document'],
 'data': ["wizard/payment_order_create_view.xml",
          "views/payment_register_view.xml",
          "views/payment_register_line_view.xml",
          'security/ir.model.access.csv',
          ],
 'auto_install': False,
 'installable': True,
 'images': []
 }
