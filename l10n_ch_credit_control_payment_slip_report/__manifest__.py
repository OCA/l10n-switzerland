# -*- coding: utf-8 -*-
{"name": "Switzerland - Printing of dunning ISR",
 "summary": "Print ISR slip related to credit control",
 "version": "10.0.1.0.0",
 "author": "Camptocamp,Odoo Community Association (OCA)",
 "category": "Localization",
 "website": "https://github.com/OCA/l10n-switzerland",
 "license": "AGPL-3",
 "depends": ["account_credit_control",
             "account_credit_control_dunning_fees",
             "l10n_ch_payment_slip"],
 "data": ["views/credit_control_printer_view.xml",
          "views/report.xml",
          "security/ir.model.access.csv"],
 "active": True,
 'installable': True
 }
